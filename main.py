from datetime import datetime
from time import sleep

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from supermemory import APIConnectionError, APIStatusError

from smriti.clients.llm import (
    create_answerer,
    create_structurer,
    create_summarizer,
    create_transcriber,
    create_vision_extractor,
)
from smriti.clients.memory import create_memory_provider
from smriti.config import get_settings
from smriti.models import (
    AskRequest,
    AskResponse,
    DemoLoadResponse,
    MemoryEntry,
    MemoryBatch,
    MemoryCheckResponse,
    PreviewRequest,
    PreviewResponse,
    RetrievalEvalRequest,
    RetrievalEvalResponse,
    RetrievalEvalResult,
    SaveResponse,
    Source,
    StatusResponse,
    SummaryRequest,
    SummaryResponse,
    TranscriptionResponse,
    MemoryUpdate,
    Persona,
)
from smriti.providers import (
    AnswerProvider,
    MemoryProvider,
    STTProvider,
    StructurerProvider,
    SummaryProvider,
)
from smriti.retrieval import expected_terms_match
from smriti.services.demo_data import demo_eval_questions, demo_memories
from smriti.services.document_ingestion import DocumentExtractor, DocumentIngestionError
from smriti.services.memory_quality import memory_quality, save_unique_memories
from smriti.services.retrieval_service import retrieve_memories


FRONTEND_DIR = Path(__file__).parent / "frontend"


def create_app(
    *,
    structurer: StructurerProvider | None = None,
    memory: MemoryProvider | None = None,
    answerer: AnswerProvider | None = None,
    summarizer: SummaryProvider | None = None,
    transcriber: STTProvider | None = None,
    document_extractor=None,
) -> FastAPI:
    app = FastAPI(title="Smriti API", version="0.1.0")
    if (FRONTEND_DIR / "src").exists():
        app.mount(
            "/assets",
            StaticFiles(directory=FRONTEND_DIR / "src"),
            name="frontend-assets",
        )
    settings = None

    needs_settings = (
        structurer is None
        or memory is None
        or answerer is None
        or summarizer is None
        or transcriber is None
        or document_extractor is None
    ) and (structurer is None or memory is None or answerer is None)

    if needs_settings:
        settings = get_settings()
        structurer = structurer or create_structurer(settings)
        memory = memory or create_memory_provider(settings)
        answerer = answerer or create_answerer(settings)
        summarizer = summarizer or create_summarizer(settings)
        transcriber = transcriber or create_transcriber(settings)
        document_extractor = document_extractor or DocumentExtractor(
            create_vision_extractor(settings)
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/status", response_model=StatusResponse)
    def app_status() -> StatusResponse:
        supermemory_ok, detail = memory.status()
        memory_mode = getattr(memory, "mode", getattr(settings, "memory_mode", "test"))
        memory_target = getattr(
            memory,
            "target",
            getattr(settings, "effective_supermemory_base_url", "test"),
        )
        groq_ok = bool(settings.groq_api_key and settings.groq_model) if settings else True
        return StatusResponse(
            api="ok",
            supermemory="ok" if supermemory_ok else "error",
            groq="configured" if groq_ok else "missing",
            memory_mode=memory_mode,
            memory_target=memory_target or "Supermemory Cloud",
            detail=detail,
        )

    @app.post("/status/memory-check", response_model=MemoryCheckResponse)
    def memory_check() -> MemoryCheckResponse:
        mode = getattr(memory, "mode", getattr(settings, "memory_mode", "test"))
        target = getattr(
            memory,
            "target",
            getattr(settings, "effective_supermemory_base_url", "test"),
        ) or "Supermemory Cloud"
        marker = f"smriti deployment check {datetime.now().astimezone().isoformat()}"
        entry = MemoryEntry(
            text=marker,
            type="remark",
            persona="self",
            occurred_at=datetime.now().astimezone(),
            entities={"check": "deployment"},
            raw=marker,
        )
        saved_id = None
        search_ok = False
        cleanup_ok = False
        searched_count = 0
        try:
            saved_id = memory.add(entry)
            entry.id = saved_id
            results = []
            for attempt in range(3):
                results = memory.search(
                    marker,
                    Persona.SELF,
                    limit=5,
                    threshold=0.1,
                    rerank=False,
                    search_mode="hybrid",
                )
                searched_count = len(results)
                search_ok = any(result.text == marker for result in results)
                if search_ok:
                    break
                if attempt < 2:
                    sleep(0.75)
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            return MemoryCheckResponse(
                mode=mode,
                target=target,
                save_ok=bool(saved_id),
                search_ok=search_ok,
                cleanup_ok=False,
                saved_id=saved_id,
                searched_count=searched_count,
                detail=str(error),
            )
        finally:
            if saved_id:
                try:
                    memory.delete(saved_id)
                    cleanup_ok = True
                except (APIConnectionError, APIStatusError, httpx.HTTPError):
                    cleanup_ok = False

        return MemoryCheckResponse(
            mode=mode,
            target=target,
            save_ok=bool(saved_id),
            search_ok=search_ok,
            cleanup_ok=cleanup_ok,
            saved_id=saved_id,
            searched_count=searched_count,
            detail=None if search_ok and cleanup_ok else "Save worked, but search or cleanup did not confirm.",
        )

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return _home_html()

    @app.post("/ingest/preview", response_model=PreviewResponse)
    def preview(request: PreviewRequest) -> PreviewResponse:
        memories = structurer.structure(
            request.text, request.persona, request.current_datetime
        )
        memories = [
            entry if isinstance(entry, MemoryEntry) else MemoryEntry.model_validate(entry)
            for entry in memories
        ]
        try:
            existing = memory.list(request.persona, limit=100)
        except (APIConnectionError, APIStatusError, httpx.HTTPError):
            existing = []
        return PreviewResponse(
            memories=memories,
            quality=[
                memory_quality(entry, existing, memories[:index])
                for index, entry in enumerate(memories)
            ],
        )

    @app.post("/documents/preview", response_model=PreviewResponse)
    async def preview_document(
        persona: Persona = Form(...),
        current_datetime: datetime | None = Form(default=None),
        file: UploadFile = File(...),
    ) -> PreviewResponse:
        current_datetime = current_datetime or datetime.now().astimezone()
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Upload a non-empty report or prescription.",
            )
        filename = file.filename or "uploaded-document"
        content_type = file.content_type or "application/octet-stream"
        try:
            extracted = document_extractor.extract(
                content=content,
                filename=filename,
                content_type=content_type,
            )
            memories = document_extractor.structure(
                text=extracted.text,
                persona=persona,
                now=current_datetime,
                filename=filename,
                source_kind=extracted.source_kind,
                extraction_method=extracted.extraction_method,
                structurer=structurer,
            )
            existing = memory.list(persona, limit=100)
        except DocumentIngestionError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(error),
            ) from error
        except (APIConnectionError, APIStatusError, httpx.HTTPError):
            existing = []

        return PreviewResponse(
            memories=memories,
            quality=[
                memory_quality(entry, existing, memories[:index])
                for index, entry in enumerate(memories)
            ],
        )

    @app.post(
        "/memories", response_model=SaveResponse, status_code=status.HTTP_201_CREATED
    )
    def save_memories(request: MemoryBatch) -> SaveResponse:
        try:
            ids, skipped = save_unique_memories(memory, request.memories)
            return SaveResponse(ids=ids, skipped_duplicates=skipped)
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supermemory rejected the save. Check memory mode, server, and API key configuration.",
            ) from error

    @app.post("/demo/load", response_model=DemoLoadResponse)
    def load_demo() -> DemoLoadResponse:
        memories = demo_memories()
        try:
            ids, skipped = save_unique_memories(memory, memories)
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supermemory rejected the demo load. Check memory mode, server, and API key configuration.",
            ) from error
        return DemoLoadResponse(
            ids=ids,
            skipped_duplicates=skipped,
            memories=memories,
            eval_questions=demo_eval_questions(),
        )

    @app.get("/memories", response_model=list[MemoryEntry])
    def list_memories(persona: Persona, limit: int = 50) -> list[MemoryEntry]:
        try:
            memories = memory.list(persona, limit=limit)
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supermemory rejected the history request. Check memory mode, server, and API key configuration.",
            ) from error
        return memories

    @app.patch("/memories/{memory_id}", response_model=MemoryEntry)
    def update_memory(memory_id: str, request: MemoryUpdate) -> MemoryEntry:
        try:
            entry = memory.update(memory_id, request.to_entry(memory_id))
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supermemory rejected the edit. The memory may still be processing, the server may be off, or the key may be invalid.",
            ) from error
        return entry

    @app.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_memory(memory_id: str) -> None:
        try:
            memory.delete(memory_id)
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supermemory rejected the delete. The memory may still be processing, the server may be off, or the key may be invalid.",
            ) from error

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        try:
            memories, debug, _scored = retrieve_memories(memory, request)
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supermemory rejected the search. Check memory mode, server, and API key configuration.",
            ) from error
        if not memories:
            return AskResponse(
                answer="I don't have a record of that.", sources=[], debug=debug
            )

        response = answerer.answer(request.question, request.persona, memories)
        sources = [
            Source(id=entry.id, text=entry.text, occurred_at=entry.occurred_at)
            for entry in memories
        ]
        return AskResponse(answer=response, sources=sources, debug=debug)

    @app.post("/retrieval/evaluate", response_model=RetrievalEvalResponse)
    def evaluate_retrieval(request: RetrievalEvalRequest) -> RetrievalEvalResponse:
        results: list[RetrievalEvalResult] = []
        try:
            for case in request.cases:
                ask_request = AskRequest(
                    question=case.question,
                    persona=request.persona,
                    from_date=request.from_date,
                    to_date=request.to_date,
                    accept_threshold=request.accept_threshold,
                    maybe_threshold=request.maybe_threshold,
                    search_threshold=request.search_threshold,
                    search_limit=request.search_limit,
                    rerank=request.rerank,
                )
                memories, debug, scored = retrieve_memories(memory, ask_request)
                top = scored[0] if scored else None
                top_source = (
                    Source(
                        id=top.memory.id,
                        text=top.memory.text,
                        occurred_at=top.memory.occurred_at,
                    )
                    if top
                    else None
                )
                passed = None
                if case.expected_contains:
                    texts_to_check = [entry.text for entry in memories]
                    if top:
                        texts_to_check.append(top.memory.text)
                    passed = any(
                        expected_terms_match(case.expected_contains, text)
                        for text in texts_to_check
                    )
                results.append(
                    RetrievalEvalResult(
                        question=case.question,
                        expected_contains=case.expected_contains,
                        passed=passed,
                        top_match=top_source,
                        top_score=top.score if top else None,
                        accepted_count=debug.accepted_count,
                        maybe_count=debug.maybe_count,
                        rejected_count=debug.rejected_count,
                        outside_date_count=debug.outside_date_count,
                        rewritten_query=debug.rewritten_query,
                        reasons=top.reasons if top else [],
                    )
                )
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supermemory rejected the eval search. Check memory mode, server, and API key configuration.",
            ) from error

        pass_count = sum(1 for item in results if item.passed is True)
        fail_count = sum(1 for item in results if item.passed is False)
        unchecked_count = sum(1 for item in results if item.passed is None)
        return RetrievalEvalResponse(
            total=len(results),
            pass_count=pass_count,
            fail_count=fail_count,
            unchecked_count=unchecked_count,
            results=results,
        )

    @app.post("/summary", response_model=SummaryResponse)
    def visit_summary(request: SummaryRequest) -> SummaryResponse:
        try:
            memories = memory.list(request.persona, limit=100)
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supermemory rejected the summary request. Check memory mode, server, and API key configuration.",
            ) from error
        memories = [entry for entry in memories if request.includes(entry.occurred_at)]
        memories = sorted(memories, key=lambda entry: entry.occurred_at)
        sources = [
            Source(id=entry.id, text=entry.text, occurred_at=entry.occurred_at)
            for entry in memories
        ]
        if not memories:
            return SummaryResponse(
                summary="I don't have recorded facts for that date range.",
                sources=[],
                date_window=request.date_window_label(),
            )
        summary = summarizer.summarize(
            request.persona, memories, request.date_window_label()
        )
        return SummaryResponse(
            summary=summary,
            sources=sources,
            date_window=request.date_window_label(),
        )

    @app.post("/voice/transcribe", response_model=TranscriptionResponse)
    def transcribe_voice(audio: UploadFile = File(...)) -> TranscriptionResponse:
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Upload an audio recording.",
            )
        try:
            text = transcriber.transcribe(
                audio.file,
                audio.filename or "recording.webm",
                audio.content_type,
            )
        except Exception as error:
            backend = getattr(transcriber, "backend", "STT provider")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{backend} STT rejected the recording. Check your STT provider configuration.",
            ) from error
        if not text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No speech detected in the recording.",
            )
        return TranscriptionResponse(text=text)

    return app


def _home_html() -> str:
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return index.read_text(encoding="utf-8")
    return "<!doctype html><title>Smriti</title><h1>Smriti</h1><p>Frontend not found.</p>"


app = create_app()
