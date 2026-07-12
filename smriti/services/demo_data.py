from smriti.models import MemoryEntry, Persona


def demo_memories() -> list[MemoryEntry]:
    return [
        MemoryEntry(
            text="Doctor said Papa should reduce salt from today.",
            type="visit",
            persona=Persona.CARE,
            occurred_at="2026-07-11T09:00:00+05:30",
            entities={"advice": "reduce salt", "person": "Papa"},
            raw="Doctor said Papa should reduce salt from today.",
        ),
        MemoryEntry(
            text="Blood pressure was 150 over 95.",
            type="vital",
            persona=Persona.CARE,
            occurred_at="2026-07-11T11:30:00+05:30",
            entities={"vital": "blood pressure", "value": "150/95"},
            raw="Papa's BP was 150 over 95 this morning.",
        ),
        MemoryEntry(
            text="Papa had poor sleep on July 10, 2026.",
            type="symptom",
            persona=Persona.CARE,
            occurred_at="2026-07-10T00:00:00+05:30",
            entities={"symptom": "poor sleep"},
            raw="Papa had poor sleep on July 10, 2026.",
        ),
        MemoryEntry(
            text="Papa had stomach pain after dinner.",
            type="symptom",
            persona=Persona.CARE,
            occurred_at="2026-07-11T19:04:00+05:30",
            entities={"symptom": "stomach pain"},
            raw="Papa had stomach pain after dinner and took medicine.",
        ),
        MemoryEntry(
            text="Papa took medicine after dinner.",
            type="medication",
            persona=Persona.CARE,
            occurred_at="2026-07-11T19:04:00+05:30",
            entities={"medication": "medicine"},
            raw="Papa had stomach pain after dinner and took medicine.",
        ),
        MemoryEntry(
            text="Papa has a doctor follow-up next Monday.",
            type="visit",
            persona=Persona.CARE,
            occurred_at="2026-07-18T05:30:00+05:30",
            entities={"visit": "doctor follow-up"},
            raw="Papa has a doctor follow-up next Monday.",
        ),
    ]


def demo_eval_questions() -> str:
    return "\n".join(
        [
            "What did doctor say about salt? => salt",
            "What was Papa's BP? => 150",
            "When did Papa sleep badly? => poor sleep",
            "What happened after dinner? => stomach pain",
            "Did Papa take medicine? => medicine",
            "When is Papa's follow-up? => follow-up",
            "What is Papa's blood group? => blood group",
        ]
    )
