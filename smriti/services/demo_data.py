from smriti.models import MemoryEntry, Persona

ASHA_SUBJECT_ID = "asha-devi"
ASHA_SUBJECT_NAME = "Asha Devi"


def demo_memories() -> list[MemoryEntry]:
    return [
        # Prescription uploaded - Asha's BP medicine
        MemoryEntry(
            text="Asha Devi prescribed Amlodipine 5mg once daily for blood pressure.",
            type="medication",
            persona=Persona.CARE,
            subject_id=ASHA_SUBJECT_ID,
            subject_name=ASHA_SUBJECT_NAME,
            occurred_at="2026-07-01T10:00:00+05:30",
            entities={"medicine": "Amlodipine", "dose": "5mg", "frequency": "once daily", "condition": "blood pressure"},
            raw="Prescription from Dr. Mehta: Amlodipine 5mg once daily for BP. Follow-up in 3 weeks.",
        ),
        MemoryEntry(
            text="Dr. Mehta scheduled follow-up for Asha Devi on 22 July 2026.",
            type="visit",
            persona=Persona.CARE,
            subject_id=ASHA_SUBJECT_ID,
            subject_name=ASHA_SUBJECT_NAME,
            occurred_at="2026-07-01T10:00:00+05:30",
            entities={"doctor": "Dr. Mehta", "followup_date": "2026-07-22"},
            raw="Dr. Mehta follow-up in 3 weeks from 1 July 2026.",
        ),
        # First dizziness mention - 5 days ago
        MemoryEntry(
            text="Asha Devi felt dizzy in the morning and sat down for a while.",
            type="symptom",
            persona=Persona.CARE,
            subject_id=ASHA_SUBJECT_ID,
            subject_name=ASHA_SUBJECT_NAME,
            occurred_at="2026-07-07T09:15:00+05:30",
            entities={"symptom": "dizziness", "time": "morning"},
            raw="Asha said she felt chakkar aayi subah ko, had to sit down.",
        ),
        MemoryEntry(
            text="Asha Devi missed her Amlodipine dose on the morning of July 7.",
            type="medication",
            persona=Persona.CARE,
            subject_id=ASHA_SUBJECT_ID,
            subject_name=ASHA_SUBJECT_NAME,
            occurred_at="2026-07-07T09:15:00+05:30",
            entities={"medicine": "Amlodipine", "status": "missed"},
            raw="She forgot to take the BP medicine that morning.",
        ),
        # Good day in between
        MemoryEntry(
            text="Asha Devi had a good day. Ate well, walked in the garden, chatted with neighbour.",
            type="remark",
            persona=Persona.CARE,
            subject_id=ASHA_SUBJECT_ID,
            subject_name=ASHA_SUBJECT_NAME,
            occurred_at="2026-07-09T18:30:00+05:30",
            entities={"mood": "cheerful", "activity": "walking"},
            raw="Aaj Asha ji kaafi khush thi. Garden mein chali, padosi se baat ki.",
        ),
        # Second dizziness mention - 2 days ago
        MemoryEntry(
            text="Asha Devi felt dizzy again after getting up from the bed.",
            type="symptom",
            persona=Persona.CARE,
            subject_id=ASHA_SUBJECT_ID,
            subject_name=ASHA_SUBJECT_NAME,
            occurred_at="2026-07-10T07:45:00+05:30",
            entities={"symptom": "dizziness", "time": "morning", "trigger": "getting up"},
            raw="Subah uthne ke baad phir chakkar aaya. She said 'sir ghoom raha tha'.",
        ),
        MemoryEntry(
            text="Asha Devi said 'sir ghoom raha tha' – head was spinning after getting up.",
            type="remark",
            persona=Persona.CARE,
            subject_id=ASHA_SUBJECT_ID,
            subject_name=ASHA_SUBJECT_NAME,
            occurred_at="2026-07-10T07:45:00+05:30",
            entities={"quote": "sir ghoom raha tha"},
            raw="Asha's words: sir ghoom raha tha subah uthke.",
        ),
        MemoryEntry(
            text="Blood pressure measured 148/92 on July 10.",
            type="vital",
            persona=Persona.CARE,
            subject_id=ASHA_SUBJECT_ID,
            subject_name=ASHA_SUBJECT_NAME,
            occurred_at="2026-07-10T08:00:00+05:30",
            entities={"vital": "blood pressure", "value": "148/92"},
            raw="BP check karke dekha: 148/92.",
        ),
        # Today's check-in
        MemoryEntry(
            text="Asha Devi took her Amlodipine this morning. Had chai and paratha.",
            type="medication",
            persona=Persona.CARE,
            subject_id=ASHA_SUBJECT_ID,
            subject_name=ASHA_SUBJECT_NAME,
            occurred_at="2026-07-11T09:00:00+05:30",
            entities={"medicine": "Amlodipine", "status": "taken"},
            raw="Aaj dawai li. Chai paratha khaya.",
        ),
    ]


def demo_eval_questions() -> str:
    return "\n".join(
        [
            "Has Asha Devi mentioned dizziness before? => dizziness",
            "When did she last feel dizzy? => July 10",
            "What is Asha Devi's BP medicine? => Amlodipine",
            "Did she miss her medicine? => missed",
            "What was her blood pressure? => 148",
            "When is her follow-up with Dr. Mehta? => July 22",
            "What did Asha say about her head? => sir ghoom raha tha",
        ]
    )
