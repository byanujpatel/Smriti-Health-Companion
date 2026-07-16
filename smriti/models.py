from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Persona(StrEnum):
    SELF = "self"
    CARE = "care"


class MemoryType(StrEnum):
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    VITAL = "vital"
    VISIT = "visit"
    DOCUMENT = "document"
    REMARK = "remark"


class MemoryEntry(BaseModel):
    id: str | None = None
    text: str = Field(min_length=1)
    type: MemoryType
    persona: Persona
    subject_id: str | None = None
    subject_name: str | None = None
    occurred_at: datetime
    occurred_at_epoch: int | None = None
    entities: dict[str, Any] = Field(default_factory=dict)
    raw: str = Field(min_length=1)

    @model_validator(mode="after")
    def populate_defaults(self):
        self.occurred_at_epoch = int(self.occurred_at.timestamp())
        if not self.subject_id:
            self.subject_id = default_subject_id(self.persona)
        if not self.subject_name:
            self.subject_name = default_subject_name(self.subject_id)
        return self


class PreviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    persona: Persona
    subject_id: str | None = None
    subject_name: str | None = None
    current_datetime: datetime = Field(default_factory=lambda: datetime.now().astimezone())

    @model_validator(mode="after")
    def require_timezone(self):
        if self.current_datetime.tzinfo is None:
            raise ValueError("current_datetime must include a timezone offset")
        return self


class MemoryQuality(BaseModel):
    title: str
    confidence: str
    signals: list[str] = Field(default_factory=list)
    duplicate: bool = False


class PreviewResponse(BaseModel):
    memories: list[MemoryEntry]
    quality: list[MemoryQuality] = Field(default_factory=list)


class MemoryBatch(BaseModel):
    memories: list[MemoryEntry] = Field(min_length=1, max_length=20)


class MemoryUpdate(BaseModel):
    text: str = Field(min_length=1)
    type: MemoryType
    persona: Persona
    subject_id: str | None = None
    subject_name: str | None = None
    occurred_at: datetime
    entities: dict[str, Any] = Field(default_factory=dict)
    raw: str = Field(min_length=1)

    def to_entry(self, id: str) -> MemoryEntry:
        return MemoryEntry(
            id=id,
            text=self.text,
            type=self.type,
            persona=self.persona,
            subject_id=self.subject_id,
            subject_name=self.subject_name,
            occurred_at=self.occurred_at,
            entities=self.entities,
            raw=self.raw,
        )


class SaveResponse(BaseModel):
    ids: list[str]
    skipped_duplicates: int = 0


class DemoLoadResponse(BaseModel):
    ids: list[str]
    skipped_duplicates: int = 0
    memories: list[MemoryEntry]
    eval_questions: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    persona: Persona
    subject_id: str | None = None
    from_date: date | None = None
    to_date: date | None = None
    accept_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    maybe_threshold: float = Field(default=0.30, ge=0.0, le=1.0)
    search_threshold: float = Field(default=0.30, ge=0.0, le=1.0)
    search_limit: int = Field(default=50, ge=1, le=100)
    rerank: bool = True

    @model_validator(mode="after")
    def validate_date_window(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        if self.maybe_threshold > self.accept_threshold:
            raise ValueError("maybe_threshold must be less than or equal to accept_threshold")
        return self

    def includes(self, occurred_at: datetime) -> bool:
        occurred_date = occurred_at.date()
        if self.from_date and occurred_date < self.from_date:
            return False
        if self.to_date and occurred_date > self.to_date:
            return False
        return True

    def date_window_label(self) -> str | None:
        if self.from_date and self.to_date:
            return f"{self.from_date.isoformat()} to {self.to_date.isoformat()}"
        if self.from_date:
            return f"from {self.from_date.isoformat()}"
        if self.to_date:
            return f"until {self.to_date.isoformat()}"
        return None


class Source(BaseModel):
    id: str | None
    text: str
    occurred_at: datetime


class RetrievalCandidate(BaseModel):
    id: str | None
    text: str
    occurred_at: datetime
    score: float
    status: str
    reasons: list[str]


class RetrievalDebug(BaseModel):
    rewritten_query: str
    supermemory_count: int
    fallback_count: int
    outside_date_count: int
    accepted_count: int
    maybe_count: int
    rejected_count: int
    accept_threshold: float
    maybe_threshold: float
    search_threshold: float
    search_limit: int
    rerank: bool
    candidates: list[RetrievalCandidate]
    outside_date_candidates: list[RetrievalCandidate] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    debug: RetrievalDebug | None = None


class RetrievalEvalCase(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    expected_contains: str | None = Field(default=None, max_length=500)


class RetrievalEvalRequest(BaseModel):
    persona: Persona
    subject_id: str | None = None
    cases: list[RetrievalEvalCase] = Field(min_length=1, max_length=20)
    from_date: date | None = None
    to_date: date | None = None
    accept_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    maybe_threshold: float = Field(default=0.30, ge=0.0, le=1.0)
    search_threshold: float = Field(default=0.30, ge=0.0, le=1.0)
    search_limit: int = Field(default=50, ge=1, le=100)
    rerank: bool = True

    @model_validator(mode="after")
    def validate_eval_window(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        if self.maybe_threshold > self.accept_threshold:
            raise ValueError("maybe_threshold must be less than or equal to accept_threshold")
        return self


class RetrievalEvalResult(BaseModel):
    question: str
    expected_contains: str | None
    passed: bool | None
    top_match: Source | None
    top_score: float | None
    accepted_count: int
    maybe_count: int
    rejected_count: int
    outside_date_count: int
    rewritten_query: str
    reasons: list[str]


class RetrievalEvalResponse(BaseModel):
    total: int
    pass_count: int
    fail_count: int
    unchecked_count: int
    results: list[RetrievalEvalResult]


class SummaryRequest(BaseModel):
    persona: Persona
    subject_id: str | None = None
    from_date: date | None = None
    to_date: date | None = None

    @model_validator(mode="after")
    def validate_date_window(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        return self

    def includes(self, occurred_at: datetime) -> bool:
        occurred_date = occurred_at.date()
        if self.from_date and occurred_date < self.from_date:
            return False
        if self.to_date and occurred_date > self.to_date:
            return False
        return True

    def date_window_label(self) -> str:
        if self.from_date and self.to_date:
            return f"{self.from_date.isoformat()} to {self.to_date.isoformat()}"
        if self.from_date:
            return f"from {self.from_date.isoformat()}"
        if self.to_date:
            return f"until {self.to_date.isoformat()}"
        return "all dates"


class SummaryResponse(BaseModel):
    summary: str
    sources: list[Source]
    date_window: str


class TranscriptionResponse(BaseModel):
    text: str


class StatusResponse(BaseModel):
    api: str
    supermemory: str
    groq: str
    memory_mode: str
    memory_target: str
    detail: str | None = None


class MemoryCheckResponse(BaseModel):
    mode: str
    target: str
    save_ok: bool
    search_ok: bool
    cleanup_ok: bool
    saved_id: str | None = None
    searched_count: int = 0
    detail: str | None = None


def default_subject_id(persona: Persona) -> str:
    return "myself" if persona == Persona.SELF else "papa"


def default_subject_name(subject_id: str | None) -> str:
    names = {
        "papa": "Papa",
        "mummy": "Mummy",
        "myself": "Myself",
    }
    return names.get(subject_id or "", subject_id or "Unknown")
