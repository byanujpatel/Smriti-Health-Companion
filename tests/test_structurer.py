from datetime import datetime

from smriti.clients.llm import GroqStructurer
from smriti.models import Persona


class RecoveringStructurer(GroqStructurer):
    def __init__(self):
        self.responses = iter(
            [
                {
                    "memories": [
                        {
                            "text": "Papa did not sleep.",
                            "type": "symptom",
                            "persona": "care",
                            "occurred_at": "2026-07-10T22:00:00+05:30",
                            "entities": ["sleep"],
                            "raw": "Papa ko neend nahi aayi",
                        }
                    ]
                },
                {
                    "memories": [
                        {
                            "text": "Papa did not sleep.",
                            "type": "symptom",
                            "persona": "care",
                            "occurred_at": "2026-07-10T22:00:00+05:30",
                            "entities": {"symptom": "poor sleep"},
                            "raw": "Papa ko neend nahi aayi",
                        }
                    ]
                },
            ]
        )

    def _json_completion(self, system, user):
        return next(self.responses)


def test_invalid_llm_json_is_retried_once():
    structurer = RecoveringStructurer()

    memories = structurer.structure(
        "Papa ko neend nahi aayi",
        Persona.CARE,
        datetime.fromisoformat("2026-07-11T12:00:00+05:30"),
    )

    assert memories[0].entities == {"symptom": "poor sleep"}


class WrongPersonaStructurer(GroqStructurer):
    def __init__(self):
        pass

    def _json_completion(self, system, user):
        return {
            "memories": [
                {
                    "text": "Papa did not sleep.",
                    "type": "symptom",
                    "persona": "self",
                    "occurred_at": "2026-07-10T22:00:00+05:30",
                    "entities": {},
                    "raw": "Papa ko neend nahi aayi",
                }
            ]
        }


def test_requested_persona_overrides_the_llm_output():
    memories = WrongPersonaStructurer().structure(
        "Papa ko neend nahi aayi",
        Persona.CARE,
        datetime.fromisoformat("2026-07-11T12:00:00+05:30"),
    )

    assert memories[0].persona == Persona.CARE


class OffTopicStructurer(GroqStructurer):
    def __init__(self):
        pass

    def _json_completion(self, system, user):
        return {"off_topic": True, "memories": []}


def test_off_topic_text_returns_no_confirmation_cards():
    memories = OffTopicStructurer().structure(
        "What is the weather?",
        Persona.SELF,
        datetime.fromisoformat("2026-07-11T12:00:00+05:30"),
    )

    assert memories == []
