from __future__ import annotations

from datetime import datetime
from typing import BinaryIO, Protocol

from smriti.models import MemoryEntry, Persona


class MemoryProvider(Protocol):
    mode: str
    target: str

    def add(self, entry: MemoryEntry) -> str: ...

    def list(
        self, persona: Persona, limit: int = 50, subject_id: str | None = None
    ) -> list[MemoryEntry]: ...

    def update(self, id: str, entry: MemoryEntry) -> MemoryEntry: ...

    def delete(self, id: str) -> None: ...

    def status(self) -> tuple[bool, str | None]: ...

    def search(
        self,
        question: str,
        persona: Persona,
        limit: int = 20,
        threshold: float = 0.3,
        rerank: bool = True,
        search_mode: str = "hybrid",
        subject_id: str | None = None,
    ) -> list[MemoryEntry]: ...


class StructurerProvider(Protocol):
    backend: str

    def structure(
        self, raw: str, persona: Persona, now: datetime
    ) -> list[MemoryEntry]: ...


class AnswerProvider(Protocol):
    backend: str

    def answer(
        self, question: str, persona: Persona, memories: list[MemoryEntry]
    ) -> str: ...


class SummaryProvider(Protocol):
    backend: str

    def summarize(
        self,
        persona: Persona,
        memories: list[MemoryEntry],
        date_window: str,
    ) -> str: ...


class STTProvider(Protocol):
    backend: str

    def transcribe(self, audio: BinaryIO, filename: str, content_type: str) -> str: ...


class VisionProvider(Protocol):
    backend: str

    def extract(self, data_url: str, filename: str) -> str: ...
