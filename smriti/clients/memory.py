from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.parse import urlparse

import httpx
from supermemory import Supermemory

from smriti.config import Settings
from smriti.models import MemoryEntry, Persona, default_subject_id


CONTAINERS = {
    Persona.CARE: "smriti_care",
    Persona.SELF: "smriti_self",
}


class SupermemoryClient:
    def __init__(self, settings: Settings):
        self._mode = settings.memory_mode
        self._base_url = settings.effective_supermemory_base_url
        hostname = urlparse(self._base_url or "").hostname
        self._is_local = self._mode == "local"
        if self._is_local and hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError(
                "Local memory mode needs SUPERMEMORY_BASE_URL pointing to localhost."
            )
        self._http = httpx.Client(base_url=self._base_url, timeout=30) if self._is_local else None
        self._client = None if self._is_local else self._cloud_client(settings)

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def target(self) -> str:
        if self._is_local:
            return self._base_url or "local"
        return self._base_url or "Supermemory Cloud"

    def _cloud_client(self, settings: Settings) -> Supermemory:
        if self._base_url:
            return Supermemory(api_key=settings.supermemory_api_key, base_url=self._base_url)
        return Supermemory(api_key=settings.supermemory_api_key)

    def add(self, entry: MemoryEntry) -> str:
        custom_id = hashlib.sha256(
            entry.model_dump_json(exclude={"id", "occurred_at_epoch"}).encode()
        ).hexdigest()
        metadata = {
                "persona": entry.persona.value,
                "subject_id": entry.subject_id,
                "subject_name": entry.subject_name,
                "type": entry.type.value,
                "occurred_at": entry.occurred_at.isoformat(),
                "occurred_at_epoch": entry.occurred_at_epoch,
                "raw": entry.raw,
                "entities_json": json.dumps(entry.entities, sort_keys=True),
        }
        if self._is_local:
            response = self._http.post(
                "/v3/documents",
                json={
                    "content": entry.text,
                    "containerTag": CONTAINERS[entry.persona],
                    "customId": f"smriti-{custom_id}",
                    "metadata": metadata,
                    "taskType": "superrag",
                },
            )
            response.raise_for_status()
            return str(response.json()["id"])

        response = self._client.add(
            content=entry.text,
            container_tag=CONTAINERS[entry.persona],
            custom_id=f"smriti-{custom_id}",
            metadata=metadata,
            task_type="superrag",
        )
        return str(response.id)

    def list(
        self, persona: Persona, limit: int = 50, subject_id: str | None = None
    ) -> list[MemoryEntry]:
        filters = [{"key": "persona", "value": persona.value}]
        request = {
            "containerTags": [CONTAINERS[persona]],
            "includeContent": True,
            "limit": limit,
            "order": "desc",
            "sort": "createdAt",
            "filters": {"AND": filters},
        }
        if self._is_local:
            response = self._http.post("/v3/documents/list", json=request)
            response.raise_for_status()
            results = response.json().get("memories", [])
        else:
            response = self._client.documents.list(
                container_tags=[CONTAINERS[persona]],
                include_content=True,
                limit=limit,
                order="desc",
                sort="createdAt",
                filters=request["filters"],
            )
            results = response.memories
        return self._entries_from_documents(results, persona, subject_id)

    def update(self, id: str, entry: MemoryEntry) -> MemoryEntry:
        metadata = self._metadata(entry)
        if self._is_local:
            response = self._http.patch(
                f"/v3/documents/{id}",
                json={
                    "content": entry.text,
                    "containerTag": CONTAINERS[entry.persona],
                    "metadata": metadata,
                    "taskType": "superrag",
                },
            )
            response.raise_for_status()
        else:
            self._client.documents.update(
                id,
                content=entry.text,
                container_tag=CONTAINERS[entry.persona],
                metadata=metadata,
                task_type="superrag",
            )
        return entry

    def delete(self, id: str) -> None:
        if self._is_local:
            response = self._http.delete(f"/v3/documents/{id}")
            response.raise_for_status()
            return
        self._client.documents.delete(id)

    def status(self) -> tuple[bool, str | None]:
        try:
            if self._is_local:
                response = self._http.post(
                    "/v3/documents/list",
                    json={"limit": 1, "includeContent": False},
                )
                response.raise_for_status()
            else:
                self._client.documents.list(limit=1, include_content=False)
        except Exception as error:
            return False, str(error)
        return True, None

    def search(
        self,
        question: str,
        persona: Persona,
        limit: int = 20,
        threshold: float = 0.3,
        rerank: bool = True,
        search_mode: str = "hybrid",
        subject_id: str | None = None,
    ) -> list[MemoryEntry]:
        filters = [{"key": "persona", "value": persona.value}]
        request = {
            "q": question,
            "containerTag": CONTAINERS[persona],
            "limit": limit,
            "searchMode": search_mode,
            "threshold": threshold,
            "rerank": rerank,
            "filters": {"AND": filters},
        }
        if self._is_local:
            response = self._http.post("/v4/search", json=request)
            response.raise_for_status()
            results = response.json().get("results", [])
        else:
            response = self._client.search.memories(
                q=question,
                container_tag=CONTAINERS[persona],
                limit=limit,
                search_mode=search_mode,
                threshold=threshold,
                rerank=rerank,
                filters=request["filters"],
            )
            results = response.results
        entries: list[MemoryEntry] = []
        for result in results:
            data = self._result_data(result)
            metadata = data.get("metadata") or {}
            if metadata.get("persona") != persona.value:
                continue
            result_subject_id = metadata.get("subject_id") or default_subject_id(persona)
            if subject_id and result_subject_id != subject_id:
                continue
            entries.append(
                MemoryEntry(
                    id=str(data.get("id")) if data.get("id") else None,
                    text=data.get("memory")
                    or data.get("chunk")
                    or data.get("content")
                    or data.get("text"),
                    type=metadata.get("type", "remark"),
                    persona=persona,
                    subject_id=result_subject_id,
                    subject_name=metadata.get("subject_name"),
                    occurred_at=metadata["occurred_at"],
                    entities=json.loads(metadata.get("entities_json", "{}")),
                    raw=metadata.get("raw")
                    or data.get("memory")
                    or data.get("chunk")
                    or data.get("content"),
                )
            )
        return entries

    @staticmethod
    def _metadata(entry: MemoryEntry) -> dict[str, Any]:
        return {
            "persona": entry.persona.value,
            "subject_id": entry.subject_id,
            "subject_name": entry.subject_name,
            "type": entry.type.value,
            "occurred_at": entry.occurred_at.isoformat(),
            "occurred_at_epoch": entry.occurred_at_epoch,
            "raw": entry.raw,
            "entities_json": json.dumps(entry.entities, sort_keys=True),
        }

    def _entries_from_documents(
        self, documents: list[Any], persona: Persona, subject_id: str | None = None
    ) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        for document in documents:
            data = self._result_data(document)
            metadata = data.get("metadata") or {}
            if metadata.get("persona") != persona.value:
                continue
            result_subject_id = metadata.get("subject_id") or default_subject_id(persona)
            if subject_id and result_subject_id != subject_id:
                continue
            text = data.get("content") or data.get("summary") or data.get("title")
            if not text:
                continue
            entries.append(
                MemoryEntry(
                    id=str(data.get("id")) if data.get("id") else None,
                    text=text,
                    type=metadata.get("type", "remark"),
                    persona=persona,
                    subject_id=result_subject_id,
                    subject_name=metadata.get("subject_name"),
                    occurred_at=metadata["occurred_at"],
                    entities=json.loads(metadata.get("entities_json", "{}")),
                    raw=metadata.get("raw") or text,
                )
            )
        return entries

    @staticmethod
    def _result_data(result: Any) -> dict[str, Any]:
        if isinstance(result, dict):
            return result
        return result.model_dump()


def create_memory_provider(settings: Settings) -> SupermemoryClient:
    return SupermemoryClient(settings)
