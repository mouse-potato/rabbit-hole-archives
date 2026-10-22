"""Read-only, publicly grounded inquiries for the playable demo.

The inquiry layer consumes only the already-filtered client packet. It cannot
inspect ECS solution components or discover evidence on the player's behalf.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

SCENES = {
    "study": "The study is quiet. The seal's empty display space stands out beside a desk of paperwork.",
    "hall": "The hall leads toward a side door, with space to investigate along the passage.",
}


def _clean(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9\s'-]", " ", text.lower()).split())



def evidence_command(text: str, options: dict[str, Any]) -> str | None:
    """Recognize clear inspection requests for evidence visible in this room.

    This is a conservative no-model fallback, not an open-ended action parser.
    A bare, exact evidence name works; fuzzy spelling requires an inspection
    verb and a uniquely matching visible item.
    """
    normalized = _clean(text)
    requested = bool(re.search(r"\b(?:examine|inspect|study|look at|take a look at)\b", normalized))
    candidates: list[str] = []
    for item in options.get("evidence", []):
        key = str(item["key"])
        aliases = {key.replace("-", " ").lower(), str(item["name"]).lower()}
        if any(
            re.search(r"\b" + re.escape(alias) + r"\b", normalized)
            for alias in aliases
        ):
            candidates.append(key)
            continue
        if not requested:
            continue
        words = normalized.split()
        if any(
            len(alias) >= 5
            and any(
                len(word) >= 5 and SequenceMatcher(None, word, alias).ratio() >= 0.85
                for word in words
            )
            for alias in aliases
        ):
            candidates.append(key)
    if len(candidates) != 1:
        return None
    key = candidates[0]
    exact_bare = normalized in {key.replace("-", " ").lower()}
    if requested or exact_bare:
        return "examine " + key
    return None



def conversational_command(text: str, options: dict[str, Any]) -> str | None:
    """Normalize explicit player intentions to known public commands.

    Never infer an action merely from mentioning a person's name. Only the
    requested action category and uniquely matched available target may pass.
    """
    normalized = _clean(text)
    if re.search(r"\b(?:don't|do not|never|not going to)\b", normalized):
        return None
    action: tuple[str, str] | None = None
    if re.search(r"\b(?:accuse|accusing|charge|blame)\b", normalized):
        action = ("accuse", "suspects")
    elif re.search(r"\b(?:talk to|speak to|interview|ask|question)\b", normalized):
        action = ("talk to", "witnesses")
    elif re.search(r"\b(?:go to|travel to|walk to|enter|visit)\b", normalized):
        action = ("go to", "places")
    if action is None:
        return None
    verb, group = action
    matched: list[str] = []
    for item in options.get(group, []):
        key = str(item["key"])
        names = {key.replace("-", " "), str(item["name"]).lower()}
        for name in names:
            # "Porter Quill" may be addressed as either "Porter" or "Quill".
            aliases = {name}
            if group == "witnesses":
                aliases.update(name.split())
            if any(re.search(r"\b" + re.escape(alias) + r"\b", normalized) for alias in aliases):
                matched.append(key)
                break
    if len(matched) == 1:
        return verb + " " + matched[0]
    return None



_TOPIC_STOPWORDS = frozenset({
    "what", "did", "does", "do", "know", "think", "say", "said", "heard",
    "about", "anything", "something", "the", "a", "an", "of", "to",
    "from", "me", "you", "he", "she", "they", "his", "her", "their",
    "quill", "porter", "rosalind", "maid", "witness", "tell", "could",
    "would", "is", "was", "there", "on", "with",
})


def testimony_inquiry(text: str, view: dict[str, Any]) -> str | None:
    """Answer a witness-knowledge question using only testimony already heard.

    A witness's identity must be resolvable from the player's current public
    view or the key attached to previously recorded testimony.
    """
    normalized = _clean(text)
    if not (
        re.match(r"^(?:what|did|does|has|had|who|how)\b", normalized)
        and re.search(r"\b(?:know|say|said|heard|tell|mention)\b", normalized)
    ):
        return None

    names: dict[str, set[str]] = {}
    for witness in view.get("witnesses", []):
        key = str(witness["witness_key"])
        full_name = str(witness["name"]).lower()
        names[key] = {key, full_name, *full_name.split()}
    for statement in view.get("heard", []):
        key = str(statement["witness_key"])
        names.setdefault(key, {key})

    identified = [
        key for key, aliases in names.items()
        if any(re.search(r"\b" + re.escape(alias) + r"\b", normalized) for alias in aliases)
    ]
    if len(identified) != 1:
        return None

    witness_key = identified[0]
    statements = [
        item for item in view.get("heard", [])
        if item["witness_key"] == witness_key
    ]
    if not statements:
        return "You have not recorded any testimony from that witness yet."

    topics = set(normalized.split()) - _TOPIC_STOPWORDS
    if not topics:
        selected = statements
    else:
        selected = [
            item for item in statements
            if topics.intersection(_clean(str(item["statement"])).split())
            or topics.intersection(_clean(str(item.get("lead_evidence_key") or "")).split())
        ]
    if not selected:
        return "Your recorded testimony from that witness does not address that topic."
    return "Your casebook records the witness saying: " + " ".join(
        f'“{item["statement"]}”' for item in selected
    )

def inquiry(text: str, packet: dict[str, Any]) -> str | None:
    """Return an answer for supported questions; None for gameplay commands.

    Unsupported *questions* return an explicit uncertainty response rather
    than being guessed as a physical action by an LLM.
    """
    normalized = _clean(text)
    # A polite request containing an executable verb is still an action.
    # In particular, do not steal "could you ask Quill" or
    # "can I go to the hall" from the existing AI interpreter.
    if re.search(
        r"\b(?:go|travel|walk|move|enter|visit|ask|talk|speak|interview|question|"
        r"examine|inspect|look at|accuse|charge)\b",
        normalized,
    ) and re.search(r"\b(?:can|could|would|will|may|should|i|let|please|want)\b", normalized):
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

    remembered = testimony_inquiry(text, view)
    if remembered is not None:
        return remembered

    if re.match(r"^(?:where|what)\b", normalized) and re.search(
        r"\b(?:am i|room am i|location|right now)\b", normalized
    ):
        return SCENES.get(current, f"You are in {current_name}.")
    question = bool(
        re.match(
            r"^(?:who|what|where|when|why|how|does|did|can|could|is|was|tell me about)\b",
            normalized,
        )
    )
    if question:
        # Do not answer a question about a witness by returning an unrelated
        # observation just because it mentions the same evidence.
        if re.search(r"\b(?:know|heard|said|think|believe)\b", normalized):
            return "You can ask an available witness directly, or review testimony in your casebook."
        for clue in view.get("discovered", []):
            label = str(clue.get("label", "")).lower()
            if label and re.search(r"\b" + re.escape(label) + r"\b", normalized):
                return str(clue["observation"])
        return "The information recorded so far does not establish an answer to that question."
    return None
