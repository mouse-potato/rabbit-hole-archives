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
    return " ".join(re.sub(r"[^a-z0-9\s'-]", " ", text.lower().replace("’", "'")).split())


def action_text(text: str) -> str:
    # Strip supported lead-ins without changing the request.
    return re.sub(
        r"^(?:please |carefully |let's |i'll |i (?:want to |would like to |will )?"
        r"|i'd like to |(?:can|could|may|would) (?:i|you) )+",
        "", _clean(text),
    ).removesuffix(" please")


_ACCUSATION = r"(?:accuse|charge|j'accuse)"
_MOVEMENT = r"(?:(?:go|move|travel|walk)(?: back)?(?: to| into)?|enter|visit)"
_EXIT_QUESTION = (
    r"(?:where can i go(?: from here)?|where (?:does|can) .+ connect to|"
    r"(?:what|where) (?:are|is) (?:the |my )?(?:exits?|ways? out)(?: from here)?)"
)


def is_accusation(text: str) -> bool:
    return bool(re.match(rf"^{_ACCUSATION}\b", action_text(text)))


def place_aliases(place: dict[str, str]) -> set[str]:
    aliases = {_clean(place["key"].replace("-", " ")), _clean(place["name"]).removeprefix("the ")}
    if "hall" in aliases or "hallway" in aliases:
        aliases.update(("hall", "hallway"))
    return aliases


def movement_target(text: str) -> str | None:
    match = re.fullmatch(rf"{_MOVEMENT} (.+)", action_text(text))
    return match[1].removeprefix("the ") if match else None


def available_destinations(packet: dict[str, Any]) -> list[dict[str, str]]:
    # This demo's navigation supports every listed room. The side door is
    # scene description only and is absent from the playable destinations.
    return [
        place for place in packet["options"]["places"]
        if place["key"] != packet["view"]["place_key"]
    ]


def request_problem(text: str) -> str | None:
    """Decline negated, conditional, or compound actions before any inference.

    This is a conservative supported-command boundary, not a general natural
    language parser. Unclear requests need a new explicit player instruction.
    """
    normalized = _clean(text)
    categories = {
        "examine": r"\b(?:examine|inspect|look at|look around)\b",
        "talk": r"\b(?:talk to|talk with|speak to|speak with|interview|ask|question)\b",
        "move": r"\b(?:go|move|travel|walk|enter|visit)\b",
        "accuse": rf"\b(?:{_ACCUSATION}|accusing|blame)\b",
    }
    requested = {key for key, pattern in categories.items() if re.search(pattern, normalized)}
    if re.match(r"^leave\b", action_text(text)):
        requested.add("move")
    if not requested and re.search(r"\bstudy\b", normalized):
        requested.add("examine")
    if not requested:
        return None
    if re.search(r"\b(?:don't|dont|do not|never|not|won't|will not|without|avoid|cancel|stop)\b", normalized):
        return "No action taken. State the action you want to carry out."
    if re.search(r"\b(?:if|unless|maybe|might|should i)\b", normalized):
        return "No action taken. Give a definite action when you are ready."
    action_words = rf"(?:examine|inspect|study|look at|look around|talk|speak|interview|ask|question|go|move|travel|walk|enter|visit|leave|{_ACCUSATION}|blame)"
    another_action = re.search(
        r"(?:\b(?:and|then|or)\b|[;,])\s*(?:i\s+)?" + action_words + r"\b",
        text.lower(),
    )
    # Conjunctions in a witness topic are allowed (e.g. Halloran and Ada).
    # Conjunctions in the requested target are ambiguous and must not select
    # the first matching entity through the lower-level prefix parser.
    target_part = re.split(r"\b(?:about|regarding|concerning)\b", normalized, maxsplit=1)[0]
    multiple_targets = re.search(r"\b(?:and|or|then)\b", target_part)
    if len(requested) > 1 or another_action or multiple_targets:
        return "No action taken. Request one action and one target at a time."
    return None



def evidence_command(text: str, options: dict[str, Any]) -> str | None:
    """Recognize clear inspection requests for evidence visible in this room.

    This is a conservative no-model fallback, not an open-ended action parser.
    A bare, exact evidence name works; fuzzy spelling requires an inspection
    verb and a uniquely matching visible item.
    """
    normalized = _clean(text)
    target = re.fullmatch(r"(?:examine|inspect|study|look at|take a look at) (.+)", action_text(text))
    requested = target is not None
    if target and re.fullmatch(
        r"(?:the )?(?:paperwork(?: on (?:the )?desk)?|desk paperwork)", target[1],
    ):
        # The scene describes the receipt as desk paperwork. This alias is
        # useful only while that particular exhibit is available to inspect.
        if any(item["key"] == "receipt" for item in options.get("evidence", [])):
            return "examine receipt"

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
    target = re.fullmatch(rf"{_ACCUSATION} (.+)", action_text(text))
    if target:
        name = target[1].removeprefix("the ").removeprefix("suspect ")
        suspects = [
            item["key"] for item in options.get("suspects", [])
            if name in {
                _clean(item["name"]), _clean(item["key"].replace("-", " ")),
                _clean(item["name"]).split()[-1],
            }
        ]
        return f"accuse {suspects[0]}" if len(suspects) == 1 else None
    if is_accusation(text):
        return None
    if not re.search(r"\b(?:talk to|speak to|interview|ask|question)\b", normalized):
        return None
    matched: list[str] = []
    for item in options.get("witnesses", []):
        key = str(item["key"])
        names = {key.replace("-", " "), str(item["name"]).lower()}
        for name in names:
            # "Porter Quill" may be addressed as either "Porter" or "Quill".
            aliases = {name}
            aliases.update(name.split())
            if any(re.search(r"\b" + re.escape(alias) + r"\b", normalized) for alias in aliases):
                matched.append(key)
                break
    if len(matched) == 1:
        return "talk to " + matched[0]
    return None



_TOPIC_STOPWORDS = frozenset({
    "what", "did", "does", "do", "know", "think", "say", "said", "heard", "hear",
    "about", "anything", "something", "the", "a", "an", "of", "to",
    "from", "me", "you", "he", "she", "they", "his", "her", "their",
    "witness", "tell", "could",
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
        and re.search(r"\b(?:know|say|said|heard|hear|see|saw|tell|mention)\b", normalized)
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

    if re.search(r"\b(?:anything else|something else|more details)\b", normalized):
        return "Your recorded testimony from that witness does not address that topic. Try asking them about a specific lead."
    topics = set(normalized.split()) - _TOPIC_STOPWORDS
    for alias in names[witness_key]:
        topics.difference_update(alias.split())
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
    view = packet["view"]
    options = packet["options"]
    current = str(view.get("place_key", ""))
    current_name = str(view.get("place_name", "this room"))
    command = action_text(text)
    destinations = available_destinations(packet)
    leave = re.fullmatch(r"leave(?: (.+))?", command)
    if re.fullmatch(_EXIT_QUESTION, normalized) or (
        leave and (leave[1] is None or any(
            place["key"] == current and leave[1].removeprefix("the ") in place_aliases(place)
            for place in options.get("places", [])
        ))
    ):
        if destinations:
            names = ", ".join(place["name"] for place in destinations)
            return f"From {current_name}, you can go to {names}. Name your destination to move."
        return "There are no other playable locations from here."

    room_request = re.fullmatch(
        r"(?:look around(?: (.+))?|(?:examine|inspect|look at) (.+))", command,
    )
    room_target = (room_request[1] or room_request[2] or "room") if room_request else ""
    room_target = room_target.removeprefix("the ")
    scene_inspection = room_target in {"room", "room i'm in", "room i am in", "current room", "surroundings", "here"}
    if room_target:
        for place in options.get("places", []):
            if room_target not in place_aliases(place):
                continue
            if place["key"] != current:
                return f"You are in {current_name}. Visit {place['name']} to look around there."
            scene_inspection = True

    if re.match(r"^compliment\b", command):
        return "You can question witnesses about the case. Social exchanges like compliments have no authored response."

    # A request for someone else's exact reply is different from asking about
    # a topic. Shared names alone cannot establish what that person said.
    if re.match(r"^ask .+ what (?:he|she|they) heard .+ say\b", command):
        return (
            "Your recorded testimony does not establish what was said in reply. "
            "You can ask the witness about a specific topic or review your casebook."
        )

    if re.fullmatch(r"what (?:can|could) (?:i|we) (?:examine|inspect|look at)(?: (?:here|in this room))?", normalized):
        names = ", ".join(item["name"] for item in options.get("evidence", []))
        return f"You can examine {names} here." if names else "There is nothing available to examine here."

    # A polite request containing an executable verb is still an action.
    # In particular, do not steal "could you ask Quill" or
    # "can I go to the hall" from the existing AI interpreter.
    if not scene_inspection and re.search(
        r"\b(?:go|travel|walk|move|enter|visit|ask|talk|speak|interview|question|"
        r"examine|inspect|look at|accuse|charge)\b",
        normalized,
    ) and re.search(r"\b(?:can|could|would|will|may|should|i|let|please|want)\b", normalized):
        return None

    if normalized in {"help", "what can i do", "what should i do next", "available actions"}:
        commands = [f"examine {item['key']}" for item in options.get("evidence", [])]
        commands.extend(f"talk to {item['witness_key']}" for item in view.get("witnesses", []))
        commands.extend(f"go to {item['key']}" for item in options.get("places", [])
                        if item["key"] != current)
        commands.extend(["review casebook", "review leads"])
        return (
            "Available commands here: " + "; ".join(commands) + ". "
            "During a conversation, ask 'what about <topic>?'. "
            "When ready, use 'accuse <suspect>'. "
            "Use 'restart investigation' to begin the authored case again."
        )

    if normalized in {"review leads", "what leads do i have", "show leads"}:
        discovered_keys = {item["evidence_key"] for item in view.get("discovered", [])}
        visible_keys = {item["key"] for item in options.get("evidence", [])}
        leads = sorted({
            (str(item["lead_evidence_key"]), str(item["witness_key"]))
            for item in view.get("heard", []) if item.get("lead_evidence_key")
        })
        if not leads:
            return "You have no leads recorded from witness testimony yet."
        lines = []
        for key, witness in leads:
            status = ("examined" if key in discovered_keys else
                      "available to examine here" if key in visible_keys else
                      "not available to examine here")
            lines.append(f"{key} (from {witness}): {status}")
        return "Your recorded leads: " + "; ".join(lines) + "."

    scene_question = (
        scene_inspection or normalized in {"look around", "describe the room", "describe the scene", "where am i"}
        or bool(re.match(r"^(?:what|what's|what is|describe|tell me about|is there anything else)\b", normalized))
        and bool(re.search(r"\b(?:here|room|scene|surroundings|around me|study|hall|hallway)\b", normalized))
    )
    # Descriptions may answer only for people visible in the current packet.
    # No facts about distant witnesses or sealed case details are projected.
    appearance = bool(re.search(
        r"\b(?:look like|appearance|describe|wearing|dressed)\b", normalized,
    ))
    if appearance:
        for witness in view.get("witnesses", []):
            name = str(witness["name"]).lower()
            key = str(witness["witness_key"])
            aliases = {key, name, *name.split()}
            if any(re.search(r"\b" + re.escape(alias) + r"\b", normalized)
                   for alias in aliases):
                description = packet.get("witness_descriptions", {}).get(key)
                if description:
                    return str(description)

    remembered = testimony_inquiry(text, view)
    if remembered is not None:
        return remembered

    if scene_question:
        other = "hall" if current == "study" else "study"
        if not scene_inspection and re.search(r"\b" + (r"hall(?:way)?" if other == "hall" else other) + r"\b", normalized):
            return f"You are in {current_name}. You would need to visit the {other} to inspect it."
        items = [str(item["name"]) for item in options.get("evidence", [])]
        people = [
            str(item["name"]) for item in view.get("witnesses", [])
        ]
        detail = str(packet.get("scene_description") or SCENES.get(current, f"You are in {current_name}."))
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

    if re.match(r"^(?:where|what)\b", normalized) and re.search(
        r"\b(?:am i|room am i|location|right now)\b", normalized
    ):
        return str(packet.get("scene_description") or SCENES.get(current, f"You are in {current_name}."))
    if re.search(r"\b(?:culprit|guilty|criminal|stole)\b", normalized) and not is_accusation(text):
        if not re.match(r"^(?:who|what|why|how|did|is)\b", normalized):
            return "You can weigh that theory against your casebook. To submit a formal accusation, use 'accuse <suspect>'."
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

