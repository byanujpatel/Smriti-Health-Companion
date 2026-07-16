from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from main import create_app
from smriti.models import MemoryEntry
from smriti.config import Settings


class FakeStructurer:
    def structure(self, raw: str, persona: str, now: datetime):
        return [
            {
                "text": "Papa had trouble sleeping last night.",
                "type": "symptom",
                "persona": persona,
                "occurred_at": "2026-07-10T22:00:00+05:30",
                "entities": {},
                "raw": raw,
            }
        ]


class FakeMemory:
    def __init__(self):
        self.saved = []
        self.search_returns_empty = False
        self.last_search = None

    def add(self, entry):
        self.saved.append(entry)
        return f"memory-{len(self.saved)}"

    def search(
        self,
        question,
        persona,
        limit=20,
        threshold=0.3,
        rerank=True,
        search_mode="hybrid",
    ):
        self.last_search = {
            "question": question,
            "persona": persona,
            "limit": limit,
            "threshold": threshold,
            "rerank": rerank,
            "search_mode": search_mode,
        }
        if self.search_returns_empty:
            return []
        return [entry for entry in self.saved if entry.persona == persona]

    def list(self, persona, limit=50):
        return [entry for entry in self.saved if entry.persona == persona][:limit]

    def update(self, id, entry):
        for index, saved in enumerate(self.saved):
            if saved.id == id:
                self.saved[index] = entry
                return entry
        raise ValueError("not found")

    def delete(self, id):
        self.saved = [entry for entry in self.saved if entry.id != id]

    def status(self):
        return True, None


class FakeAnswerer:
    def answer(self, question, persona, memories):
        if not memories:
            return "I don't have a record of that."
        return "Papa had trouble sleeping on July 10, 2026. [2026-07-10]"


class FakeSummarizer:
    def summarize(self, persona, memories, date_window):
        return (
            f"Recorded facts summary for {date_window}\n"
            "- Symptoms timeline: Papa had trouble sleeping.\n"
            "- Questions to ask the doctor: Ask whether the sleep pattern matters."
        )


class FakeTranscriber:
    def transcribe(self, audio, filename, content_type):
        return "Papa ko kal raat neend nahi aayi."


class FakeDocumentExtractor:
    def extract(self, *, content, filename, content_type):
        return SimpleNamespace(
            text="Metformin 500 mg twice daily. Follow-up next Monday.",
            source_kind="pdf" if content_type == "application/pdf" else "photo",
            extraction_method="pypdf" if content_type == "application/pdf" else "vision",
        )

    def structure(
        self,
        *,
        text,
        persona,
        now,
        filename,
        source_kind,
        extraction_method,
        structurer,
    ):
        return [
            MemoryEntry(
                text="Metformin 500 mg twice daily",
                type="medication",
                persona=persona,
                occurred_at=now,
                entities={
                    "medicine": "Metformin",
                    "dose": "500 mg",
                    "frequency": "twice daily",
                    "source_filename": filename,
                    "source_kind": source_kind,
                    "extraction_method": extraction_method,
                },
                raw=text,
            ),
            MemoryEntry(
                text="Follow-up next Monday",
                type="visit",
                persona=persona,
                occurred_at=now,
                entities={
                    "source_filename": filename,
                    "source_kind": source_kind,
                    "extraction_method": extraction_method,
                },
                raw=text,
            ),
        ]


def app_with_fakes(memory=None):
    return create_app(
        structurer=FakeStructurer(),
        memory=memory or FakeMemory(),
        answerer=FakeAnswerer(),
        summarizer=FakeSummarizer(),
        transcriber=FakeTranscriber(),
        document_extractor=FakeDocumentExtractor(),
    )


def test_user_previews_confirms_and_recalls_a_health_log():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)

    preview = client.post(
        "/ingest/preview",
        json={"text": "Papa ko kal raat neend nahi aayi", "persona": "care"},
    )

    assert preview.status_code == 200
    cards = preview.json()["memories"]
    assert cards[0]["text"] == "Papa had trouble sleeping last night."
    assert memory.saved == []

    saved = client.post("/memories", json={"memories": cards})
    assert saved.status_code == 201
    assert saved.json() == {"ids": ["memory-1"], "skipped_duplicates": 0}
    memory.saved[0].id = saved.json()["ids"][0]

    answer = client.post(
        "/ask", json={"question": "When did Papa sleep badly?", "persona": "care"}
    )
    assert answer.status_code == 200
    assert answer.json()["answer"].endswith("[2026-07-10]")
    assert answer.json()["sources"][0]["occurred_at"].startswith("2026-07-10")


def test_empty_retrieval_has_a_fixed_non_hallucinated_answer():
    app = create_app(
        structurer=FakeStructurer(), memory=FakeMemory(), answerer=FakeAnswerer()
    )
    client = TestClient(app)

    response = client.post(
        "/ask", json={"question": "What is Papa's blood group?", "persona": "care"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "I don't have a record of that."
    assert body["sources"] == []
    assert body["debug"]["accepted_count"] == 0
    assert body["debug"]["outside_date_count"] == 0
    assert body["debug"]["candidates"] == []


def test_preview_returns_memory_quality_signals():
    app = app_with_fakes()
    client = TestClient(app)

    response = client.post(
        "/ingest/preview",
        json={"text": "Papa ko kal raat neend nahi aayi", "persona": "care"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["quality"][0]["title"] == "Symptom noted"
    assert body["quality"][0]["confidence"] in {"high", "review"}
    assert "symptom" in body["quality"][0]["signals"]
    assert body["quality"][0]["duplicate"] is False


def test_save_skips_duplicate_memory_cards():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)
    preview = client.post(
        "/ingest/preview",
        json={"text": "Papa ko kal raat neend nahi aayi", "persona": "care"},
    ).json()
    card = preview["memories"][0]

    first = client.post("/memories", json={"memories": [card]})
    second = client.post("/memories", json={"memories": [card]})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["ids"] == ["memory-1"]
    assert second.json() == {"ids": [], "skipped_duplicates": 1}
    assert len(memory.saved) == 1


def test_demo_load_creates_sample_memories_and_questions():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)

    response = client.post("/demo/load")

    body = response.json()
    assert response.status_code == 200
    assert len(body["ids"]) == 6
    assert body["skipped_duplicates"] == 0
    assert len(body["memories"]) == 6
    assert "What was Papa's BP? => 150" in body["eval_questions"]
    assert len(memory.saved) == 6


def test_demo_load_skips_duplicates_on_second_run():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)

    client.post("/demo/load")
    response = client.post("/demo/load")

    body = response.json()
    assert response.status_code == 200
    assert body["ids"] == []
    assert body["skipped_duplicates"] == 6
    assert len(memory.saved) == 6


def test_personas_are_isolated_during_retrieval():
    memory = FakeMemory()
    app = create_app(
        structurer=FakeStructurer(), memory=memory, answerer=FakeAnswerer()
    )
    client = TestClient(app)
    care_card = client.post(
        "/ingest/preview",
        json={"text": "Papa did not sleep", "persona": "care"},
    ).json()["memories"][0]
    client.post("/memories", json={"memories": [care_card]})

    response = client.post(
        "/ask", json={"question": "When did I sleep badly?", "persona": "self"}
    )

    body = response.json()
    assert body["answer"] == "I don't have a record of that."
    assert body["sources"] == []
    assert body["debug"]["accepted_count"] == 0
    assert body["debug"]["fallback_count"] == 0
    assert body["debug"]["candidates"] == []


def test_ask_filters_retrieved_memories_by_date_window():
    memory = FakeMemory()
    app = create_app(
        structurer=FakeStructurer(), memory=memory, answerer=FakeAnswerer()
    )
    client = TestClient(app)
    card = client.post(
        "/ingest/preview",
        json={"text": "Papa did not sleep", "persona": "care"},
    ).json()["memories"][0]
    client.post("/memories", json={"memories": [card]})

    response = client.post(
        "/ask",
        json={
            "question": "When did Papa sleep badly?",
            "persona": "care",
            "from_date": "2026-07-11",
            "to_date": "2026-07-11",
        },
    )

    body = response.json()
    assert body["answer"] == "I don't have a record of that."
    assert body["sources"] == []
    assert body["debug"]["accepted_count"] == 0
    assert body["debug"]["outside_date_count"] == 1
    assert body["debug"]["outside_date_candidates"][0]["text"] == "Papa had trouble sleeping last night."


def test_ask_rejects_backwards_date_window():
    app = create_app(
        structurer=FakeStructurer(), memory=FakeMemory(), answerer=FakeAnswerer()
    )
    client = TestClient(app)

    response = client.post(
        "/ask",
        json={
            "question": "What happened?",
            "persona": "care",
            "from_date": "2026-07-12",
            "to_date": "2026-07-11",
        },
    )

    assert response.status_code == 422


def test_retrieval_eval_reports_pass_fail_and_unchecked_cases():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)
    card = client.post(
        "/ingest/preview",
        json={"text": "Papa ko kal raat neend nahi aayi", "persona": "care"},
    ).json()["memories"][0]
    client.post("/memories", json={"memories": [card]})
    memory.saved[0].id = "memory-1"

    response = client.post(
        "/retrieval/evaluate",
        json={
            "persona": "care",
            "cases": [
                {
                    "question": "When did Papa sleep badly?",
                    "expected_contains": "trouble sleeping",
                },
                {
                    "question": "What was Papa blood group?",
                    "expected_contains": "blood group",
                },
                {"question": "Any sleep memory?"},
            ],
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 3
    assert body["pass_count"] == 1
    assert body["fail_count"] == 1
    assert body["unchecked_count"] == 1
    assert body["results"][0]["top_match"]["id"] == "memory-1"
    assert body["results"][0]["accepted_count"] == 1
    assert body["results"][1]["passed"] is False
    assert body["results"][2]["passed"] is None


def test_retrieval_eval_passes_when_expected_words_match_top_memory():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)
    card = {
        "id": "memory-sleep",
        "text": "Papa had poor sleep on July 10, 2026.",
        "type": "symptom",
        "persona": "care",
        "occurred_at": "2026-07-10T00:00:00+05:30",
        "entities": {"symptom": "poor sleep"},
        "raw": "Papa had poor sleep on July 10, 2026.",
    }
    client.post("/memories", json={"memories": [card]})
    memory.saved[0].id = "memory-sleep"

    response = client.post(
        "/retrieval/evaluate",
        json={
            "persona": "care",
            "cases": [
                {
                    "question": "When did Papa sleep badly?",
                    "expected_contains": "trouble sleeping",
                }
            ],
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["pass_count"] == 1
    assert body["fail_count"] == 0
    assert body["results"][0]["passed"] is True
    assert body["results"][0]["top_match"]["id"] == "memory-sleep"


def test_blood_group_query_does_not_match_blood_pressure_memory():
    memory = FakeMemory()
    memory.search_returns_empty = True
    app = create_app(
        structurer=FakeStructurer(), memory=memory, answerer=FakeAnswerer()
    )
    client = TestClient(app)
    card = {
        "id": "memory-bp",
        "text": "Blood pressure was 150 over 95",
        "type": "vital",
        "persona": "care",
        "occurred_at": "2026-07-11T08:00:00+05:30",
        "entities": {"vital": "blood pressure", "value": "150/95"},
        "raw": "Blood pressure was 150 over 95",
    }
    client.post("/memories", json={"memories": [card]})
    memory.saved[0].id = "memory-bp"

    response = client.post(
        "/ask",
        json={
            "question": "What is Papa's blood group?",
            "persona": "care",
            "accept_threshold": 0.45,
            "maybe_threshold": 0.3,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["answer"] == "I don't have a record of that."
    assert body["sources"] == []
    assert body["debug"]["accepted_count"] == 0


def test_retrieval_eval_uses_dynamic_search_settings():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)

    response = client.post(
        "/retrieval/evaluate",
        json={
            "persona": "care",
            "search_threshold": 0.8,
            "search_limit": 7,
            "rerank": False,
            "cases": [{"question": "salt advice"}],
        },
    )

    assert response.status_code == 200
    assert memory.last_search["threshold"] == 0.8
    assert memory.last_search["limit"] == 7
    assert memory.last_search["rerank"] is False
    assert memory.last_search["search_mode"] == "hybrid"


def test_home_page_loads_phase_two_ui():
    app = create_app(
        structurer=FakeStructurer(), memory=FakeMemory(), answerer=FakeAnswerer()
    )
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Smriti" in response.text
    assert "react" in response.text.lower()


def test_memory_history_lists_saved_persona_records():
    memory = FakeMemory()
    app = create_app(
        structurer=FakeStructurer(), memory=memory, answerer=FakeAnswerer()
    )
    client = TestClient(app)
    card = client.post(
        "/ingest/preview",
        json={"text": "Papa did not sleep", "persona": "care"},
    ).json()["memories"][0]
    client.post("/memories", json={"memories": [card]})
    memory.saved[0].id = "memory-1"

    response = client.get("/memories?persona=care")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "memory-1"
    assert response.json()[0]["persona"] == "care"


def test_saved_memory_can_be_edited_and_deleted():
    memory = FakeMemory()
    app = create_app(
        structurer=FakeStructurer(), memory=memory, answerer=FakeAnswerer()
    )
    client = TestClient(app)
    card = client.post(
        "/ingest/preview",
        json={"text": "Papa did not sleep", "persona": "care"},
    ).json()["memories"][0]
    client.post("/memories", json={"memories": [card]})
    memory.saved[0].id = "memory-1"

    edited = client.patch(
        "/memories/memory-1",
        json={
            "text": "Papa slept better after dinner.",
            "type": "remark",
            "persona": "care",
            "occurred_at": "2026-07-10T22:00:00+05:30",
            "entities": {},
            "raw": "Papa slept better after dinner.",
        },
    )

    assert edited.status_code == 200
    assert edited.json()["text"] == "Papa slept better after dinner."

    deleted = client.delete("/memories/memory-1")

    assert deleted.status_code == 204
    assert memory.saved == []


def test_status_reports_dependencies():
    app = create_app(
        structurer=FakeStructurer(), memory=FakeMemory(), answerer=FakeAnswerer()
    )
    client = TestClient(app)

    response = client.get("/status")

    assert response.status_code == 200
    assert response.json()["api"] == "ok"
    assert response.json()["supermemory"] == "ok"
    assert response.json()["memory_mode"] == "test"
    assert response.json()["memory_target"] == "test"
    assert response.json()["llm_backend"] == "test"
    assert response.json()["vision_backend"] == "test"
    assert response.json()["stt_backend"] == "test"
    assert response.json()["fully_local"] is False


def test_cloud_mode_ignores_localhost_base_url():
    settings = Settings(
        smriti_memory_mode="cloud",
        supermemory_base_url="http://localhost:6767",
        supermemory_api_key="sm_test",
        groq_api_key="gsk_test",
    )

    assert settings.effective_supermemory_base_url is None


def test_fully_local_requires_all_local_providers():
    hybrid = Settings(
        smriti_memory_mode="local",
        smriti_llm_backend="groq",
        smriti_vision_backend="groq",
        smriti_stt_backend="groq",
        supermemory_api_key="sm_test",
        groq_api_key="gsk_test",
    )
    local = Settings(
        smriti_memory_mode="local",
        smriti_llm_backend="ollama",
        smriti_vision_backend="ollama",
        smriti_stt_backend="parakeet",
        supermemory_api_key="sm_test",
        groq_api_key="gsk_test",
    )

    assert hybrid.fully_local is False
    assert local.fully_local is True


def test_memory_check_saves_searches_and_cleans_up():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)

    response = client.post("/status/memory-check")

    body = response.json()
    assert response.status_code == 200
    assert body["save_ok"] is True
    assert body["search_ok"] is True
    assert body["cleanup_ok"] is True
    assert body["searched_count"] == 1
    assert memory.saved == []


def test_visit_summary_uses_saved_memories_in_date_range():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)
    card = client.post(
        "/ingest/preview",
        json={"text": "Papa did not sleep", "persona": "care"},
    ).json()["memories"][0]
    client.post("/memories", json={"memories": [card]})
    memory.saved[0].id = "memory-1"

    response = client.post(
        "/summary",
        json={
            "persona": "care",
            "from_date": "2026-07-10",
            "to_date": "2026-07-10",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["date_window"] == "2026-07-10 to 2026-07-10"
    assert "Recorded facts summary" in body["summary"]
    assert body["sources"][0]["id"] == "memory-1"


def test_visit_summary_empty_range_has_fixed_answer():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)

    response = client.post(
        "/summary",
        json={
            "persona": "care",
            "from_date": "2026-07-12",
            "to_date": "2026-07-12",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "summary": "I don't have recorded facts for that date range.",
        "sources": [],
        "date_window": "2026-07-12 to 2026-07-12",
    }


def test_voice_transcription_returns_text():
    app = app_with_fakes()
    client = TestClient(app)

    response = client.post(
        "/voice/transcribe",
        files={"audio": ("recording.webm", b"fake audio", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "Papa ko kal raat neend nahi aayi."}


def test_voice_transcription_rejects_non_audio_upload():
    app = app_with_fakes()
    client = TestClient(app)

    response = client.post(
        "/voice/transcribe",
        files={"audio": ("notes.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 415


def test_document_upload_previews_cards_without_saving():
    memory = FakeMemory()
    app = app_with_fakes(memory)
    client = TestClient(app)

    response = client.post(
        "/documents/preview",
        data={
            "persona": "care",
            "current_datetime": "2026-07-18T09:00:00+05:30",
        },
        files={"file": ("prescription.pdf", b"%PDF fake", "application/pdf")},
    )

    body = response.json()
    assert response.status_code == 200
    assert len(body["memories"]) == 2
    assert body["memories"][0]["type"] == "medication"
    assert body["memories"][0]["text"] == "Metformin 500 mg twice daily"
    assert body["memories"][0]["entities"]["source_filename"] == "prescription.pdf"
    assert body["memories"][0]["entities"]["extraction_method"] == "pypdf"
    assert memory.saved == []


def test_photo_upload_uses_document_preview_flow():
    app = app_with_fakes()
    client = TestClient(app)

    response = client.post(
        "/documents/preview",
        data={"persona": "care"},
        files={"file": ("rx.jpg", b"fake image", "image/jpeg")},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["memories"][0]["entities"]["source_kind"] == "photo"
    assert body["memories"][0]["entities"]["extraction_method"] == "vision"


def test_fallback_history_answers_when_supermemory_search_misses_synonym():
    memory = FakeMemory()
    memory.search_returns_empty = True
    app = create_app(
        structurer=FakeStructurer(), memory=memory, answerer=FakeAnswerer()
    )
    client = TestClient(app)
    card = {
        "id": "memory-bp",
        "text": "Papa's BP was 150 over 95 this morning.",
        "type": "vital",
        "persona": "care",
        "occurred_at": "2026-07-11T08:00:00+05:30",
        "entities": {"vital": "blood pressure", "value": "150/95"},
        "raw": "Papa's BP was 150 over 95 this morning.",
    }
    client.post("/memories", json={"memories": [card]})
    memory.saved[0].id = "memory-bp"

    response = client.post(
        "/ask", json={"question": "What was Papa's pressure?", "persona": "care"}
    )

    body = response.json()
    assert body["sources"][0]["id"] == "memory-bp"
    assert body["debug"]["supermemory_count"] == 0
    assert body["debug"]["fallback_count"] == 1
    assert body["debug"]["accepted_count"] == 1
    assert body["debug"]["candidates"][0]["score"] >= 0.45


def test_threshold_rejects_weak_match_even_if_history_has_memories():
    memory = FakeMemory()
    memory.search_returns_empty = True
    app = create_app(
        structurer=FakeStructurer(), memory=memory, answerer=FakeAnswerer()
    )
    client = TestClient(app)
    card = {
        "id": "memory-salt",
        "text": "Doctor said Papa should reduce salt from today.",
        "type": "remark",
        "persona": "care",
        "occurred_at": "2026-07-11T08:00:00+05:30",
        "entities": {},
        "raw": "Doctor said Papa should reduce salt from today.",
    }
    client.post("/memories", json={"memories": [card]})

    response = client.post(
        "/ask",
        json={
            "question": "What is Papa's blood group?",
            "persona": "care",
            "accept_threshold": 0.45,
            "maybe_threshold": 0.3,
        },
    )

    body = response.json()
    assert body["answer"] == "I don't have a record of that."
    assert body["sources"] == []
    assert body["debug"]["accepted_count"] == 0


def test_ask_passes_dynamic_supermemory_search_parameters():
    memory = FakeMemory()
    app = create_app(
        structurer=FakeStructurer(), memory=memory, answerer=FakeAnswerer()
    )
    client = TestClient(app)

    response = client.post(
        "/ask",
        json={
            "question": "What was Papa's pressure?",
            "persona": "care",
            "search_threshold": 0.6,
            "search_limit": 7,
            "rerank": False,
        },
    )

    assert response.status_code == 200
    assert memory.last_search["threshold"] == 0.6
    assert memory.last_search["limit"] == 7
    assert memory.last_search["rerank"] is False
    assert memory.last_search["search_mode"] == "hybrid"
    assert response.json()["debug"]["search_threshold"] == 0.6
    assert response.json()["debug"]["search_limit"] == 7
    assert response.json()["debug"]["rerank"] is False


def test_ask_uses_rewritten_query_for_supermemory_search():
    memory = FakeMemory()
    app = create_app(
        structurer=FakeStructurer(), memory=memory, answerer=FakeAnswerer()
    )
    client = TestClient(app)

    response = client.post(
        "/ask", json={"question": "Papa ko namak ka kya bola?", "persona": "care"}
    )

    assert response.status_code == 200
    assert memory.last_search["question"] != "Papa ko namak ka kya bola?"
    assert "sodium" in memory.last_search["question"]
    assert response.json()["debug"]["rewritten_query"] == memory.last_search["question"]


def test_symptom_synonyms_match_hinglish_terms_in_history_fallback():
    memory = FakeMemory()
    memory.search_returns_empty = True
    app = create_app(
        structurer=FakeStructurer(), memory=memory, answerer=FakeAnswerer()
    )
    client = TestClient(app)
    card = {
        "id": "memory-breath",
        "text": "Papa had breathlessness while climbing stairs.",
        "type": "symptom",
        "persona": "care",
        "occurred_at": "2026-07-11T08:00:00+05:30",
        "entities": {"symptom": "breathlessness"},
        "raw": "Papa ko seedhi chadhte waqt saans phool rahi thi.",
    }
    client.post("/memories", json={"memories": [card]})
    memory.saved[0].id = "memory-breath"

    response = client.post(
        "/ask", json={"question": "Papa ko saans ka issue tha?", "persona": "care"}
    )

    body = response.json()
    assert body["sources"][0]["id"] == "memory-breath"
    assert body["debug"]["accepted_count"] == 1
