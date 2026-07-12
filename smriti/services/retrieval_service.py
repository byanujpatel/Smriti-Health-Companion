from smriti.models import (
    AskRequest,
    MemoryEntry,
    RetrievalCandidate,
    RetrievalDebug,
)
from smriti.retrieval import accepted_memories, rewrite_query, score_memories


def retrieve_memories(memory, request: AskRequest):
    rewritten_query = rewrite_query(request.question)
    supermemory_memories = memory.search(
        rewritten_query,
        request.persona,
        limit=request.search_limit,
        threshold=request.search_threshold,
        rerank=request.rerank,
    )
    history_memories = memory.list(request.persona, limit=request.search_limit)
    outside_date_candidates = dedupe_memories(
        [
            *[entry for entry in supermemory_memories if not request.includes(entry.occurred_at)],
            *[entry for entry in history_memories if not request.includes(entry.occurred_at)],
        ]
    )
    supermemory_memories = [
        entry for entry in supermemory_memories if request.includes(entry.occurred_at)
    ]
    history_memories = [
        entry for entry in history_memories if request.includes(entry.occurred_at)
    ]
    candidates = dedupe_memories([*supermemory_memories, *history_memories])
    scored = score_memories(
        request.question,
        candidates,
        accept_threshold=request.accept_threshold,
        maybe_threshold=request.maybe_threshold,
    )
    outside_date_scored = score_memories(
        request.question,
        outside_date_candidates,
        accept_threshold=request.accept_threshold,
        maybe_threshold=request.maybe_threshold,
    )
    debug = retrieval_debug(
        scored,
        supermemory_count=len(supermemory_memories),
        fallback_count=len(history_memories),
        accept_threshold=request.accept_threshold,
        maybe_threshold=request.maybe_threshold,
        search_threshold=request.search_threshold,
        search_limit=request.search_limit,
        rerank=request.rerank,
        rewritten_query=rewritten_query,
        outside_date_scored=outside_date_scored,
    )
    return accepted_memories(scored), debug, scored


def dedupe_memories(memories: list[MemoryEntry]) -> list[MemoryEntry]:
    seen: set[str] = set()
    deduped: list[MemoryEntry] = []
    for entry in memories:
        key = entry.id or f"{entry.persona.value}:{entry.occurred_at.isoformat()}:{entry.text}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def retrieval_debug(
    scored,
    *,
    supermemory_count: int,
    fallback_count: int,
    accept_threshold: float,
    maybe_threshold: float,
    search_threshold: float,
    search_limit: int,
    rerank: bool,
    rewritten_query: str,
    outside_date_scored,
) -> RetrievalDebug:
    return RetrievalDebug(
        rewritten_query=rewritten_query,
        supermemory_count=supermemory_count,
        fallback_count=fallback_count,
        outside_date_count=sum(1 for item in outside_date_scored if item.status in {"accepted", "maybe"}),
        accepted_count=sum(1 for item in scored if item.status == "accepted"),
        maybe_count=sum(1 for item in scored if item.status == "maybe"),
        rejected_count=sum(1 for item in scored if item.status == "rejected"),
        accept_threshold=accept_threshold,
        maybe_threshold=maybe_threshold,
        search_threshold=search_threshold,
        search_limit=search_limit,
        rerank=rerank,
        candidates=[
            RetrievalCandidate(
                id=item.memory.id,
                text=item.memory.text,
                occurred_at=item.memory.occurred_at,
                score=item.score,
                status=item.status,
                reasons=item.reasons,
            )
            for item in scored[:10]
        ],
        outside_date_candidates=[
            RetrievalCandidate(
                id=item.memory.id,
                text=item.memory.text,
                occurred_at=item.memory.occurred_at,
                score=item.score,
                status=item.status,
                reasons=item.reasons,
            )
            for item in outside_date_scored
            if item.status in {"accepted", "maybe"}
        ][:5],
    )
