import json
from datetime import datetime

import httpx

from smriti.clients.llm import (
    OllamaStructurer,
    OllamaVisionExtractor,
    create_answerer,
    create_structurer,
    create_summarizer,
    create_transcriber,
    create_vision_extractor,
)
from smriti.config import Settings
from smriti.models import Persona


def local_settings() -> Settings:
    return Settings(
        smriti_memory_mode="local",
        smriti_llm_backend="ollama",
        smriti_vision_backend="ollama",
        smriti_stt_backend="groq",
        supermemory_api_key="sm_test",
        groq_api_key="gsk_test",
        ollama_text_model="qwen2.5:7b",
        ollama_vision_model="llama3.2-vision:11b",
    )


def test_local_provider_factories_select_ollama_and_groq_stt():
    settings = local_settings()

    assert create_structurer(settings).backend == "ollama"
    assert create_answerer(settings).backend == "ollama"
    assert create_summarizer(settings).backend == "ollama"
    assert create_vision_extractor(settings).backend == "ollama"
    assert create_transcriber(settings).backend == "groq"


def test_ollama_structurer_uses_json_chat_payload():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": json.dumps(
                        {
                            "memories": [
                                {
                                    "text": "Papa had poor sleep.",
                                    "type": "symptom",
                                    "persona": "care",
                                    "occurred_at": "2026-07-10T22:00:00+05:30",
                                    "entities": {"symptom": "poor sleep"},
                                    "raw": "Papa ko neend nahi aayi",
                                }
                            ]
                        }
                    )
                }
            },
        )

    structurer = OllamaStructurer(local_settings())
    structurer._http = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://ollama.test",
    )

    memories = structurer.structure(
        "Papa ko neend nahi aayi",
        Persona.CARE,
        datetime.fromisoformat("2026-07-11T12:00:00+05:30"),
    )

    assert memories[0].text == "Papa had poor sleep."
    assert requests[0]["model"] == "qwen2.5:7b"
    assert requests[0]["format"] == "json"
    assert requests[0]["stream"] is False


def test_ollama_vision_sends_base64_image_payload():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"content": "Metformin 500 mg"}})

    extractor = OllamaVisionExtractor(local_settings())
    extractor._http = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://ollama.test",
    )

    text = extractor.extract("data:image/png;base64,abc123", "rx.png")

    assert text == "Metformin 500 mg"
    assert requests[0]["model"] == "llama3.2-vision:11b"
    assert requests[0]["messages"][1]["images"] == ["abc123"]
