from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from time import sleep
import logging
import smtplib
from email.mime.text import MIMEText

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from supermemory import APIConnectionError, APIStatusError

logger = logging.getLogger(__name__)

from smriti.clients.llm import (
    create_answerer,
    create_checkin_structurer,
    create_pattern_detector,
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
    CheckInRequest,
    CheckInResponse,
    DemoLoadResponse,
    MemoryEntry,
    MemoryBatch,
    MemoryCheckResponse,
    PatternRequest,
    PatternsResponse,
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


def apply_subject(
    entry: MemoryEntry, subject_id: str | None, subject_name: str | None
) -> MemoryEntry:
    if subject_id:
        entry.subject_id = subject_id
    if subject_name:
        entry.subject_name = subject_name
    return MemoryEntry.model_validate(entry.model_dump())


def create_app(
    *,
    structurer: StructurerProvider | None = None,
    memory: MemoryProvider | None = None,
    answerer: AnswerProvider | None = None,
    summarizer: SummaryProvider | None = None,
    transcriber: STTProvider | None = None,
    document_extractor=None,
    checkin_structurer=None,
    pattern_detector=None,
) -> FastAPI:
    # Mutable containers so inner functions can mutate them without nonlocal
    _ctx: dict = {"settings": None, "bot_app": None}

    @asynccontextmanager
    async def lifespan(application: FastAPI):  # noqa: ARG001
        # startup: register Telegram webhook if bot + webhook URL are configured
        bot_app = _ctx["bot_app"]
        cfg = _ctx["settings"]
        if bot_app and cfg and cfg.webhook_url:
            webhook_target = f"{cfg.webhook_url.rstrip('/')}/telegram"
            try:
                await bot_app.bot.set_webhook(
                    url=webhook_target,
                    allowed_updates=["message", "callback_query"],
                )
                logger.info("Telegram webhook set → %s", webhook_target)
            except Exception as exc:
                logger.warning("Could not set Telegram webhook: %s", exc)
        yield
        # shutdown (nothing to do)

    app = FastAPI(title="Smriti API", version="0.1.0", lifespan=lifespan)
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
        checkin_structurer = checkin_structurer or create_checkin_structurer(settings)
        pattern_detector = pattern_detector or create_pattern_detector(settings)
        _ctx["settings"] = settings

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
            apply_subject(
                entry if isinstance(entry, MemoryEntry) else MemoryEntry.model_validate(entry),
                request.subject_id,
                request.subject_name,
            )
            for entry in memories
        ]
        try:
            existing = memory.list(
                request.persona, limit=100, subject_id=request.subject_id
            )
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
        subject_id: str | None = Form(default=None),
        subject_name: str | None = Form(default=None),
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
            memories = [
                apply_subject(entry, subject_id, subject_name) for entry in memories
            ]
            existing = memory.list(persona, limit=100, subject_id=subject_id)
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
    def list_memories(
        persona: Persona, limit: int = 50, subject_id: str | None = None
    ) -> list[MemoryEntry]:
        try:
            memories = memory.list(persona, limit=limit, subject_id=subject_id)
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
                    subject_id=request.subject_id,
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
            memories = memory.list(
                request.persona, limit=100, subject_id=request.subject_id
            )
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

    @app.post("/checkin", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
    def checkin(request: CheckInRequest) -> CheckInResponse:
        checkin_summary, memories = checkin_structurer.structure_checkin(
            transcript=request.transcript,
            subject_name=request.subject_name,
            now=request.current_datetime,
        )
        for entry in memories:
            entry.subject_id = request.subject_id
            entry.subject_name = request.subject_name
            entry = MemoryEntry.model_validate(entry.model_dump())
        try:
            ids, _skipped = save_unique_memories(memory, memories)
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supermemory rejected the check-in save. Check memory mode and API key.",
            ) from error
        return CheckInResponse(summary=checkin_summary, memories=memories, saved_ids=ids)

    @app.post("/patterns", response_model=PatternsResponse)
    def get_patterns(request: PatternRequest) -> PatternsResponse:
        cutoff = datetime.now().astimezone() - timedelta(days=request.days)
        try:
            all_memories = memory.list(Persona.CARE, limit=200, subject_id=request.subject_id)
        except (APIConnectionError, APIStatusError, httpx.HTTPError) as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supermemory rejected the pattern request. Check memory mode and API key.",
            ) from error
        recent = [m for m in all_memories if m.occurred_at >= cutoff]
        if not recent:
            return PatternsResponse(
                patterns=[],
                date_range=f"last {request.days} days",
            )
        date_range = f"last {request.days} days"
        patterns = pattern_detector.detect_patterns(recent, date_range)
        return PatternsResponse(patterns=patterns, date_range=date_range)

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

    # ── Caregiver Dashboard ────────────────────────────────────────────────────

    @app.get("/api/dashboard/{subject_id}")
    def get_dashboard(subject_id: str) -> dict:
        """Caregiver summary: recent memories, flags, urgency for a parent."""
        try:
            all_memories = memory.list(Persona.CARE, limit=100, subject_id=subject_id)
        except (APIConnectionError, APIStatusError, httpx.HTTPError):
            all_memories = []

        all_memories = sorted(all_memories, key=lambda m: m.occurred_at, reverse=True)

        last_checkin_at = all_memories[0].occurred_at.isoformat() if all_memories else None
        flags = _extract_flags(all_memories[:15])
        urgency = _score_urgency(all_memories[:15])

        recent = [
            {
                "id": m.id,
                "text": m.text,
                "type": m.type,
                "occurred_at": m.occurred_at.isoformat(),
            }
            for m in all_memories[:12]
        ]

        return {
            "subject_id": subject_id,
            "last_checkin_at": last_checkin_at,
            "memory_count": len(all_memories),
            "flags": flags,
            "urgency": urgency,
            "recent_memories": recent,
        }

    # ── Emergency Alert ────────────────────────────────────────────────────────

    @app.post("/api/emergency")
    def emergency_alert(
        subject_id: str = Form(...),
        subject_name: str = Form(...),
        message: str = Form(default="Emergency alert triggered"),
    ) -> dict:
        """Log an emergency memory and optionally send an alert email."""
        entry = MemoryEntry(
            text=f"EMERGENCY: {message}",
            type="remark",
            persona=Persona.CARE,
            subject_id=subject_id,
            subject_name=subject_name,
            occurred_at=datetime.now().astimezone(),
            entities={"urgency": "emergency", "source": "web"},
            raw=message,
        )
        try:
            save_unique_memories(memory, [entry])
        except (APIConnectionError, APIStatusError, httpx.HTTPError):
            pass  # Log failure silently — alert message is more important

        if settings and settings.alert_email:
            _send_emergency_email(subject_name, message, settings.alert_email, settings)

        return {"status": "alert_sent", "subject_name": subject_name}

    # ── Telegram Webhook ──────────────────────────────────────────────────────

    if settings and settings.telegram_bot_token:
        from telegram import Update as TgUpdate
        from telegram_bot import build_bot_app as _build_bot

        _bot_app = _build_bot(settings.telegram_bot_token)
        _ctx["bot_app"] = _bot_app

        @app.post("/telegram")
        async def telegram_webhook(request: Request) -> dict:
            data = await request.json()
            update = TgUpdate.de_json(data, _bot_app.bot)
            await _bot_app.process_update(update)
            return {"ok": True}

    return app


def _home_html() -> str:
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return index.read_text(encoding="utf-8")
    return "<!doctype html><title>Smriti</title><h1>Smriti</h1><p>Frontend not found.</p>"


# ── Dashboard helpers (module-level so they can be tested) ────────────────────

_FLAG_RULES = [
    ("dizziness",     ["dizzi", "chakkar", "chakker", "giddiness", "vertigo", "sir ghoom"]),
    ("missed_medicine", ["missed", "nahi li", "bhool", "forgot medicine", "skipped", "dawa nahi"]),
    ("pain",          ["dard", " pain", "ache", "tez dard", "chest pain", "seene mein"]),
    ("fall",          ["gir ", "fell", "fall", " gira", "slipped", "girane"]),
    ("poor_sleep",    ["neend nahi", "insomnia", "nahi soyi", "couldn't sleep", "so nahi"]),
    ("bp_elevated",   ["bp high", "bp 15", "bp 16", "bp 17", "bp 18", "blood pressure high"]),
]


def _extract_flags(memories: list) -> list[dict]:
    """Rule-based flag extraction from recent memories. No LLM — instant."""
    seen: set[str] = set()
    flags = []
    for m in memories:
        combined = (m.text + " " + m.raw).lower()
        for flag_name, keywords in _FLAG_RULES:
            if flag_name not in seen and any(k in combined for k in keywords):
                seen.add(flag_name)
                flags.append({
                    "flag": flag_name,
                    "label": flag_name.replace("_", " ").title(),
                    "from_memory": m.text[:80],
                    "date": m.occurred_at.isoformat(),
                })
    return flags


def _score_urgency(memories: list) -> dict:
    """Rule-based urgency score 1-5. No LLM — instant."""
    score = 1
    reasons: list[str] = []
    for m in memories:
        t = (m.text + " " + m.raw).lower()
        if any(k in t for k in ["chest pain", "breathing", "saans nahi", "emergency", "gir gayi", "gir gaya"]):
            score = max(score, 5)
            reasons.append("Serious symptom or emergency")
        elif any(k in t for k in ["chakkar", "dizzi", "gira", "fell", "bp 15", "bp 16", "bp 17", "bp 18"]):
            score = max(score, 3)
            reasons.append("Attention needed")
        elif any(k in t for k in ["missed", "bhool", "nahi li", "skipped"]):
            score = max(score, 2)
            reasons.append("Missed medicine")
    level = {1: "green", 2: "blue", 3: "yellow", 4: "orange", 5: "red"}.get(min(score, 5), "green")
    return {"score": score, "level": level, "reasons": list(dict.fromkeys(reasons))}


def _send_emergency_email(subject_name: str, message: str, to_email: str, settings) -> None:
    """Send a plain-text emergency email via Gmail SMTP. Silent on failure."""
    smtp_user = settings.smtp_user
    smtp_pass = settings.smtp_pass
    if not smtp_user or not smtp_pass:
        return
    try:
        body = (
            f"SMRITI EMERGENCY ALERT\n\n"
            f"{subject_name} needs attention.\n"
            f"Message: {message}\n"
            f"Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
            f"Open Smriti to view full memory timeline."
        )
        msg = MIMEText(body)
        msg["Subject"] = f"🆘 Smriti Emergency: {subject_name}"
        msg["From"] = smtp_user
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
    except Exception as exc:
        logger.warning("Emergency email failed: %s", exc)


app = create_app()
