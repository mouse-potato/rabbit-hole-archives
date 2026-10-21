"""Read-only, publicly grounded inquiries for the playable demo.

The inquiry layer consumes only the already-filtered client packet. It cannot
inspect ECS solution components or discover evidence on the player's behalf.
"""
from __future__ import annotations

import re
from typing import Any

SCENES = {
    "study": "The study is quiet. The seal's empty display space stands out beside a desk of paperwork.",
    "hall": "The hall leads toward a side door, with space to investigate along the passage.",
}


def _clean(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9\s'-]", " ", text.lower()).split())


def inquiry(text: str, packet: dict[str, Any]) -> str | None:
    """Return an answer for supported questions; None for gameplay commands.

    Unsupported *questions* return an explicit uncertainty response rather
    than being guessed as a physical action by an LLM.
    """
    normalized = _clean(text)
    # A polite request containing an executable verb is still an action.
    # In particular, do not steal "could you ask Quill" or
    # "can I go to the hall" from the existing AI interpreter.
    if re.match(r"^(?:can|could|would|will|may|should)\\b", normalized) and re.search(
        r"\\b(?:go|travel|walk|move|enter|visit|ask|talk|speak|interview|question|"
        r"examine|inspect|look at|accuse|charge)\\b",
        normalized,
    ):
        return None
    view = packet["view"]
    options = packet["options"]
    current = str(view.get("place_key", ""))
    current_name = str(view.get("place_name", "this room"))

    scene_question = (
        normalized in {"look around", "describe the room", "describe the scene", "where am i"}
        or bool(re.match(r"^(?:what|what's|what is|describe|tell me about)\b", normalized))
        and bool(re.search(r"\b(?:here|room|scene|surroundings|around me|study|hall)\b", normalized))
    )
    if scene_question:
        other = "hall" if current == "study" else "study"
        if re.search(r"\b" + re.escape(other) + r"\b", normalized):
            return f"You are in {current_name}. You would need to visit the {other} to inspect it."
        items = [str(item["name"]) for item in options.get("evidence", [])]
        people = [
            str(item["name"]) for item in view.get("witnesses", [])
        ]
        detail = SCENES.get(current, f"You are in {current_name}.")
        if items:
            detail += " You can examine: " + ", ".join(items) + "."
        if people:
            detail += " You can question: " + ", ".join(people) + "."
        return detail

    if normalized in {"review my evidence", "what have i found", "what do i know", "review casebook"}:
        discovered = view.get("discovered", [])
        heard = view.get("heard", [])
        if not discovered and not heard:
            return "Your casebook contains no recorded evidence or testimony yet."
        summary = [f"{item['label']}: {item['observation']}" for item in discovered]
        summary.extend(str(item["statement"]) for item in heard)
        return "Your casebook records: " + " ".join(summary)

    question = bool(
        re.match(
            r"^(?:who|what|where|when|why|how|does|did|can|could|is|was|tell me about)\b",
            normalized,
        )
    )
    if question:
        for clue in view.get("discovered", []):
            label = str(clue.get("label", "")).lower()
            if label and re.search(r"\b" + re.escape(label) + r"\b", normalized):
                return str(clue["observation"])
        return "The information recorded so far does not establish an answer to that question."
    return None
