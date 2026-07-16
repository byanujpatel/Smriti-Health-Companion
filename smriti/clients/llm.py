import json
from datetime import datetime
from typing import BinaryIO

from groq import Groq
from pydantic import ValidationError

from smriti.config import Settings
from smriti.models import MemoryEntry, Persona


SAFETY_RULES = """You are a health memory tool, not a medical adviser.
Never diagnose, recommend medication or doses, interpret results as good or bad,
or make urgency judgments. Only structure, recall, and summarize recorded facts."""


class _GroqClient:
    backend = "groq"

    def __init__(self, settings: Settings):
        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    def _json_completion(self, system: str, user: str) -> dict:
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        return json.loads(completion.choices[0].message.content or "{}")


class GroqStructurer(_GroqClient):
    def structure(
        self, raw: str, persona: Persona, now: datetime
    ) -> list[MemoryEntry]:
        system = f"""{SAFETY_RULES}
Convert a health log, including Hinglish, into strict JSON with a top-level
`memories` array and an `off_topic` boolean. Split multiple facts. Normalize `text` to English and preserve
the input in `raw`. Allowed types: symptom, medication, vital, visit, document,
remark. Resolve relative dates using the supplied current datetime. Treat `kal`
as yesterday for past-tense health logs. Do not add medical interpretation.
If the input contains no health-related fact, return {{"off_topic": true, "memories": []}}.
Each item requires: text, type, persona, occurred_at, entities, raw.
`entities` must always be a JSON object, such as {{"symptom": "poor sleep"}},
or an empty object {{}}. Never return an array for `entities`."""
        request = json.dumps(
            {
                "raw": raw,
                "persona": persona.value,
                "current_datetime": now.isoformat(),
            }
        )
        try:
            payload = self._json_completion(system, request)
            return self._validate(payload, persona)
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as error:
            try:
                retry_payload = self._json_completion(
                    system,
                    f"{request}\nYour previous response failed validation: {error}. Return corrected JSON only.",
                )
                return self._validate(retry_payload, persona)
            except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
                return [
                    MemoryEntry(
                        text=raw,
                        type="remark",
                        persona=persona,
                        occurred_at=now,
                        entities={},
                        raw=raw,
                    )
                ]

    @staticmethod
    def _validate(payload: dict, persona: Persona) -> list[MemoryEntry]:
        if payload.get("off_topic") is True:
            return []
        memories = payload.get("memories")
        if not isinstance(memories, list) or not memories:
            raise ValueError("memories must be a non-empty array")
        validated = []
        for item in memories:
            item = {**item, "persona": persona.value}
            validated.append(MemoryEntry.model_validate(item))
        return validated


class GroqAnswerer(_GroqClient):
    def answer(
        self, question: str, persona: Persona, memories: list[MemoryEntry]
    ) -> str:
        persona_tone = (
            "Refer warmly and operationally to the parent."
            if persona == Persona.CARE
            else "Use second person and an analytical tone."
        )
        system = f"""{SAFETY_RULES}
{persona_tone}
Answer only from the supplied memories. Cite every factual claim using the
memory date in [YYYY-MM-DD] form. If the records do not answer the question,
say exactly: I don't have a record of that. Prefer later entries when records
conflict."""
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": question,
                            "memories": [
                                {
                                    "id": memory.id,
                                    "text": memory.text,
                                    "occurred_at": memory.occurred_at.isoformat(),
                                }
                                for memory in memories
                            ],
                        }
                    ),
                },
            ],
            temperature=0,
        )
        return completion.choices[0].message.content or "I don't have a record of that."


class GroqSummarizer(_GroqClient):
    def summarize(
        self,
        persona: Persona,
        memories: list[MemoryEntry],
        date_window: str,
    ) -> str:
        persona_context = (
            "The summary is for a caregiver preparing notes about a parent."
            if persona == Persona.CARE
            else "The summary is for the person preparing their own health notes."
        )
        system = f"""{SAFETY_RULES}
{persona_context}
Create a doctor-visit preparation summary only from supplied records.
Do not diagnose, interpret values as good/bad, recommend medicines, recommend
doses, or make urgency judgments. Say "No recorded items" for empty sections.
Questions must be phrased as questions to ask the doctor, not advice."""
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "date_window": date_window,
                            "required_format": [
                                "Recorded facts summary",
                                "Symptoms timeline",
                                "Vitals",
                                "Medicines or changes",
                                "Doctor advice or visits",
                                "Questions to ask the doctor",
                                "Source dates",
                            ],
                            "memories": [
                                {
                                    "text": memory.text,
                                    "type": memory.type.value,
                                    "occurred_at": memory.occurred_at.isoformat(),
                                }
                                for memory in memories
                            ],
                        }
                    ),
                },
            ],
            temperature=0,
        )
        return completion.choices[0].message.content or "No recorded items."


class GroqTranscriber(_GroqClient):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._stt_model = settings.groq_stt_model

    def transcribe(self, audio: BinaryIO, filename: str, content_type: str) -> str:
        transcription = self._client.audio.transcriptions.create(
            model=self._stt_model,
            file=(filename, audio, content_type),
            response_format="json",
            temperature=0,
            prompt=(
                "Transcribe short health logs. Preserve Hinglish words such as "
                "Papa, BP, dawa, namak, neend, saans, bukhar."
            ),
        )
        text = getattr(transcription, "text", None)
        return (text or "").strip()


class GroqVisionExtractor(_GroqClient):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._vision_model = settings.groq_vision_model

    def extract(self, data_url: str, filename: str) -> str:
        completion = self._client.chat.completions.create(
            model=self._vision_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"{SAFETY_RULES}\n"
                        "Extract visible text from medical reports, prescriptions, lab reports, "
                        "and medicine labels. Preserve medicine names, doses, frequencies, dates, "
                        "doctor instructions, and lab values. If the image is blurry or unreadable, "
                        "say exactly: UNREADABLE."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Extract text from this medical document image: {filename}",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                },
            ],
            temperature=0,
        )
        return (completion.choices[0].message.content or "").strip()


def _unsupported_backend(kind: str, backend: str) -> NotImplementedError:
    return NotImplementedError(
        f"{kind} backend '{backend}' is configured but not implemented yet. "
        "Use Groq for Phase 11A, then add the local provider in Phase 11B."
    )


def create_structurer(settings: Settings):
    if settings.llm_backend == "groq":
        return GroqStructurer(settings)
    raise _unsupported_backend("LLM", settings.llm_backend)


def create_answerer(settings: Settings):
    if settings.llm_backend == "groq":
        return GroqAnswerer(settings)
    raise _unsupported_backend("LLM", settings.llm_backend)


def create_summarizer(settings: Settings):
    if settings.llm_backend == "groq":
        return GroqSummarizer(settings)
    raise _unsupported_backend("LLM", settings.llm_backend)


def create_transcriber(settings: Settings):
    if settings.stt_backend == "groq":
        return GroqTranscriber(settings)
    raise _unsupported_backend("STT", settings.stt_backend)


def create_vision_extractor(settings: Settings):
    if settings.vision_backend == "groq":
        return GroqVisionExtractor(settings)
    raise _unsupported_backend("Vision", settings.vision_backend)
