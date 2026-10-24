"""Deterministic topic matching shared by intent and trusted witness handlers."""
from __future__ import annotations

import re

_FILLER = frozenset({
    "what", "did", "does", "do", "know", "think", "say", "said", "heard", "hear",
    "about", "anything", "something", "the", "a", "an", "of", "to", "from",
    "me", "you", "he", "she", "they", "his", "her", "their", "witness", "tell",
    "could", "would", "is", "was", "there", "on", "with", "please", "can", "may",
    "i", "want", "like", "and", "or", "all", "everything",
})


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold()))


def interview_topic(text: str) -> str | None:
    """None means an opening interview; even an empty explicit topic is scoped."""
    parts = re.split(r"\b(?:about|regarding|concerning)\b", text, maxsplit=1, flags=re.IGNORECASE)
    return parts[1].strip() if len(parts) == 2 else None


def topic_matches(topic: str, statement: str, lead_key: str | None) -> bool:
    terms = words(topic) - _FILLER
    return bool(terms.intersection(words(statement) | words(lead_key or "")))
