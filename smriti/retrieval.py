import re
from dataclasses import dataclass

from smriti.models import MemoryEntry


ACCEPT_THRESHOLD = 0.45
MAYBE_THRESHOLD = 0.30

SYNONYMS = {
    "bp": {"bp", "pressure", "bpreading", "hypertension"},
    "pressure": {"bp", "pressure", "bpreading", "hypertension"},
    "salt": {"salt", "sodium", "namak", "low-salt", "reduce", "kam"},
    "sleep": {"sleep", "slept", "sleeping", "neend", "insomnia", "rest", "soya", "soyi"},
    "medicine": {"medicine", "medication", "tablet", "dose", "pill", "drug", "dawa", "dawai", "goli"},
    "doctor": {"doctor", "dr", "visit", "advice", "said", "consult"},
    "pain": {"pain", "ache", "headache", "dard", "migraine"},
    "sugar": {"sugar", "glucose", "diabetes", "diabetic", "hba1c"},
    "fever": {"fever", "temperature", "temp", "bukhar"},
    "swelling": {"swelling", "swollen", "sujan"},
    "breathing": {"breath", "breathing", "breathless", "breathlessness", "saans"},
    "appetite": {"appetite", "hunger", "bhook"},
    "urine": {"urine", "pee", "urination", "peshab"},
    "bowel": {"bowel", "stool", "constipation", "loose", "motion"},
    # Dizziness cluster — covers Hindi (chakkar) and all English spellings
    "dizzy": {"dizzy", "dizziness", "giddy", "giddiness", "vertigo", "chakkar", "chakker", "sir ghoom", "ghoom", "spinning"},
    "dizziness": {"dizzy", "dizziness", "giddy", "giddiness", "vertigo", "chakkar", "chakker", "sir ghoom", "ghoom", "spinning"},
    "chakkar": {"dizzy", "dizziness", "chakkar", "chakker", "sir ghoom", "ghoom", "vertigo"},
    # Fall cluster
    "fall": {"fall", "fell", "fallen", "gira", "giri", "gir", "slipped", "girane"},
    "fell": {"fall", "fell", "fallen", "gira", "giri", "gir", "slipped"},
    # Mood cluster
    "mood": {"mood", "feeling", "feel", "feels", "mahsoos", "kaise", "kaisi", "theek", "accha", "bura"},
    # Said/told cluster — for "she said her head was spinning" style queries
    "said": {"mentioned", "said", "told", "boli", "bataya"},
}

STOPWORDS = {
    "a",
    "about",
    "any",
    "blood",
    "did",
    "does",
    "for",
    "had",
    "has",
    "have",
    "her",
    "him",
    "his",
    "is",
    "it",
    "ka",
    "kya",
    "ko",
    "me",
    "mention",
    "mentioned",
    "my",
    "of",
    "papa",
    "she",
    "the",
    "tha",
    "that",
    "to",
    "was",
    "what",
    "when",
}

TYPE_HINTS = {
    "vital": {"bp", "blood", "pressure", "sugar", "glucose", "pulse", "oxygen", "spo2", "temperature", "temp", "fever"},
    "medication": {"medicine", "medication", "tablet", "dose", "pill", "dawa", "missed", "skipped", "forgot"},
    "symptom": {"pain", "ache", "sleep", "neend", "fever", "cough", "dizzy", "dizziness", "chakkar", "swelling", "breathing", "appetite", "urine", "bowel", "vertigo", "giddiness"},
    "visit": {"doctor", "dr", "visit", "appointment", "consult"},
    "remark": {"mentioned", "said", "told", "quote", "boli", "bataya"},
}


@dataclass(frozen=True)
class ScoredMemory:
    memory: MemoryEntry
    score: float
    status: str
    reasons: list[str]


def score_memories(
    question: str,
    memories: list[MemoryEntry],
    *,
    accept_threshold: float = ACCEPT_THRESHOLD,
    maybe_threshold: float = MAYBE_THRESHOLD,
) -> list[ScoredMemory]:
    scored = [
        _score_memory(question, memory, accept_threshold, maybe_threshold)
        for memory in memories
    ]
    return sorted(scored, key=lambda item: item.score, reverse=True)


def accepted_memories(scored: list[ScoredMemory]) -> list[MemoryEntry]:
    return [item.memory for item in scored if item.status == "accepted"]


def rewrite_query(question: str) -> str:
    terms = _tokens(question, keep_stopwords=True)
    expanded = _expand_terms(terms, text=question)
    additions = sorted(expanded - terms)
    if not additions:
        return question
    return f"{question} {' '.join(additions[:18])}"


def _score_memory(
    question: str,
    memory: MemoryEntry,
    accept_threshold: float,
    maybe_threshold: float,
) -> ScoredMemory:
    query_terms = _expand_terms(_tokens(question), text=question)
    text_terms = _expand_terms(
        _tokens(f"{memory.text} {memory.raw} {memory.type.value}"),
        text=f"{memory.text} {memory.raw} {memory.type.value}",
    )
    reasons: list[str] = []
    score = 0.0

    overlap = query_terms & text_terms
    if query_terms:
        overlap_score = len(overlap) / len(query_terms)
        score += min(0.55, overlap_score * 0.55)
        if overlap:
            reasons.append(f"term overlap: {', '.join(sorted(overlap)[:6])}")

    if _exact_phrase_bonus(question, memory.text):
        score += 0.20
        reasons.append("exact phrase match")

    type_terms = TYPE_HINTS.get(memory.type.value, set())
    if query_terms & type_terms:
        score += 0.15
        reasons.append(f"type hint: {memory.type.value}")

    entity_terms = _expand_terms(_tokens(" ".join(str(value) for value in memory.entities.values())))
    entity_overlap = query_terms & entity_terms
    if entity_overlap:
        score += 0.15
        reasons.append(f"entity match: {', '.join(sorted(entity_overlap)[:4])}")

    if len(overlap) >= 2:
        score += 0.10
        reasons.append("multiple matched terms")

    score = min(score, 1.0)
    status = "rejected"
    if score >= accept_threshold:
        status = "accepted"
    elif score >= maybe_threshold:
        status = "maybe"

    if not reasons:
        reasons.append("no strong lexical match")

    return ScoredMemory(memory=memory, score=round(score, 3), status=status, reasons=reasons)


def _tokens(text: str, *, keep_stopwords: bool = False) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) > 1 and (keep_stopwords or token not in STOPWORDS)
    }


def expected_terms_match(expected: str, text: str) -> bool:
    expected_terms = _expand_terms(_tokens(expected), text=expected)
    text_terms = _expand_terms(_tokens(text), text=text)
    if not expected_terms:
        return expected.lower() in text.lower()
    overlap = expected_terms & text_terms
    return bool(overlap) and len(overlap) / len(expected_terms) >= 0.5


def _expand_terms(tokens: set[str], *, text: str = "") -> set[str]:
    expanded = set(tokens)
    lower_text = text.lower()
    for token in list(tokens):
        if token == "blood" and not _mentions_blood_pressure(lower_text):
            continue
        for canonical, words in SYNONYMS.items():
            if token in words:
                expanded.add(canonical)
                expanded.update(words)
    return expanded


def _exact_phrase_bonus(question: str, text: str) -> bool:
    question_tokens = _tokens(question)
    text_lower = text.lower()
    return any(len(token) >= 4 and token in text_lower for token in question_tokens)


def _mentions_blood_pressure(text: str) -> bool:
    return bool(
        re.search(r"\bbp\b", text)
        or "blood pressure" in text
        or "pressure" in text
        or "hypertension" in text
    )
