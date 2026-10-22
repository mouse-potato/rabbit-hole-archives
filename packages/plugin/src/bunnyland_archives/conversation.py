"""Small, public-only conversation context for the single-player demo host."""
from __future__ import annotations

import re
from typing import Any


def followup_topic(text: str) -> str | None:
    """Recognize explicit follow-ups without guessing an addressee or topic."""
    normalized = " ".join(text.strip().rstrip("?.!").split())
    match = re.fullmatch(
        r"(?:what about|how about|tell me more about|"
        r"ask (?:him|her|them) about)\s+(.+)", normalized, re.IGNORECASE,
    )
    return match.group(1) if match else None


def conversation_view(witness_key: str | None, view: dict[str, Any]) -> dict[str, Any] | None:
    """Describe an active, present witness using only recorded public testimony."""
    if witness_key is None:
        return None
    witness = next((w for w in view.get("witnesses", [])
                    if w["witness_key"] == witness_key), None)
    if witness is None:
        return None
    leads = sorted({
        str(item["lead_evidence_key"])
        for item in view.get("heard", [])
        if item["witness_key"] == witness_key and item.get("lead_evidence_key")
    })
    return {"witness_key": witness_key, "name": witness["name"], "lead_topics": leads}
