import re

from smriti.models import MemoryEntry, MemoryQuality, Persona


def save_unique_memories(memory, entries: list[MemoryEntry]) -> tuple[list[str], int]:
    if not entries:
        return [], 0
    persona = entries[0].persona
    existing = memory.list(persona, limit=100)
    ids = []
    skipped = 0
    seen = set()
    for entry in entries:
        key = memory_key(entry)
        if key in seen or is_duplicate_memory(entry, existing):
            skipped += 1
            continue
        seen.add(key)
        ids.append(memory.add(entry))
        existing.append(entry)
    return ids, skipped


def memory_quality(
    entry: MemoryEntry,
    existing: list[MemoryEntry],
    earlier_preview: list[MemoryEntry],
) -> MemoryQuality:
    signals = [entry.type.value]
    if entry.occurred_at:
        signals.append("dated")
    if entry.entities:
        signals.append("key facts")
    duplicate = is_duplicate_memory(entry, [*existing, *earlier_preview])
    if duplicate:
        signals.append("duplicate")
    confidence = "high"
    if duplicate:
        confidence = "duplicate"
    elif not entry.entities or len(entry.text.split()) < 3:
        confidence = "review"
    return MemoryQuality(
        title=memory_title(entry),
        confidence=confidence,
        signals=signals,
        duplicate=duplicate,
    )


def memory_title(entry: MemoryEntry) -> str:
    if entry.type.value == "vital":
        return "Vital recorded"
    if entry.type.value == "medication":
        return "Medicine noted"
    if entry.type.value == "symptom":
        return "Symptom noted"
    if entry.type.value == "visit":
        return "Visit or follow-up"
    if entry.type.value == "document":
        return "Document note"
    return "Care note" if entry.persona == Persona.CARE else "Personal note"


def is_duplicate_memory(entry: MemoryEntry, existing: list[MemoryEntry]) -> bool:
    key = memory_key(entry)
    return any(memory_key(item) == key for item in existing)


def memory_key(entry: MemoryEntry) -> str:
    text = re.sub(r"\s+", " ", entry.text.lower()).strip()
    return f"{entry.persona.value}:{entry.type.value}:{entry.occurred_at.date().isoformat()}:{text}"
