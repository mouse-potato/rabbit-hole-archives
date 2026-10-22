"""Non-authoritative Narrator adapter: deterministic intent, safe narration input.

Two jobs, both intentionally narrow:

* turn untrusted player text into one *proposed* action (verb + target), never into a world
  mutation, and
* package what narration is allowed to see: the restricted projection plus a public subset
  of the action outcome.

Nothing here can decide the solution, mutate canonical facts, or reveal privileged fields.
An LLM may later choose the wording; it never gets more truth than this packet contains.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Literal

from bunnyland.core import (
    HandlerContext,
    HandlerResult,
    SubmittedCommand,
    parse_entity_id,
)
from pydantic import BaseModel, ConfigDict
from relics import EntityId, World

from .components import (
    ArchiveEvidenceComponent,
    ArchiveSuspectComponent,
    ArchiveWitnessComponent,
)
from .mechanics import (
    ACCUSE_COMMAND_TYPE,
    COMMAND_TYPE,
    TALK_COMMAND_TYPE,
    AccusationResolvedEvent,
    AccuseSuspectHandler,
    EvidenceExaminedEvent,
    ExamineEvidenceHandler,
    TalkToWitnessHandler,
    WitnessQuestionedEvent,
)
from .projection import ArchiveNarratorView, narrator_view
from .testimony import interview_topic

_HANDLERS: dict[
    str, type[ExamineEvidenceHandler | TalkToWitnessHandler | AccuseSuspectHandler]
] = {
    COMMAND_TYPE: ExamineEvidenceHandler,
    TALK_COMMAND_TYPE: TalkToWitnessHandler,
    ACCUSE_COMMAND_TYPE: AccuseSuspectHandler,
}

_VERBS: dict[str, tuple[str, ...]] = {
    COMMAND_TYPE: ("examine", "study", "look at", "inspect"),
    TALK_COMMAND_TYPE: ("talk to", "talk with", "question", "ask", "interview", "speak to"),
    ACCUSE_COMMAND_TYPE: ("accuse", "charge"),
}

# Words that carry no target information; dropped before matching.
_FILLER = frozenset({"the", "a", "an", "that", "this", "evidence", "suspect", "witness"})


class IntentResolution(BaseModel):
    """A proposed action derived from player text. Never an applied mutation."""

    model_config = ConfigDict(frozen=True)

    status: Literal["resolved", "unresolved"]
    command_type: str | None = None
    target_id: str | None = None
    target_key: str | None = None
    reason: str = ""
    topic: str | None = None


class NarrationOutcome(BaseModel):
    """The public part of one action outcome, safe to paraphrase."""

    model_config = ConfigDict(frozen=True)

    action: str
    accepted: bool
    detail: str = ""
    observation: str | None = None
    statements: tuple[str, ...] = ()
    verdict: str | None = None
    witness_key: str | None = None
    witness_name: str | None = None
    first_discovery: bool | None = None
    first_conversation: bool | None = None
    new_testimony: bool | None = None


class NarrationPacket(BaseModel):
    """Everything narration may see: a restricted view and a public outcome."""

    model_config = ConfigDict(frozen=True)

    view: ArchiveNarratorView
    outcome: NarrationOutcome | None = None


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s'-]", " ", text.lower()).strip()


def _targets(world: World) -> dict[str, list[tuple[str, EntityId]]]:
    """Map candidate phrases to (command type, entity) for the current world."""

    table: dict[str, list[tuple[str, EntityId]]] = {}

    def add(phrase: str, command_type: str, entity: EntityId) -> None:
        cleaned = _normalize(phrase)
        if not cleaned:
            return
        entries = table.setdefault(cleaned, [])
        if (command_type, entity) not in entries:
            entries.append((command_type, entity))

    for entity in world.query().with_all([ArchiveEvidenceComponent]).execute_entities():
        evidence = entity.get_component(ArchiveEvidenceComponent)
        add(evidence.evidence_key.replace("-", " "), COMMAND_TYPE, entity.id)
        add(evidence.evidence_key, COMMAND_TYPE, entity.id)
    for entity in world.query().with_all([ArchiveWitnessComponent]).execute_entities():
        witness = entity.get_component(ArchiveWitnessComponent)
        add(witness.witness_key.replace("-", " "), TALK_COMMAND_TYPE, entity.id)
        add(witness.name, TALK_COMMAND_TYPE, entity.id)
        # A character's last name is a natural shorthand. Collisions must
        # still resolve as ambiguous, never arbitrarily pick a witness.
        parts = witness.name.split()
        if len(parts) > 1:
            add(parts[-1], TALK_COMMAND_TYPE, entity.id)
    for entity in world.query().with_all([ArchiveSuspectComponent]).execute_entities():
        suspect = entity.get_component(ArchiveSuspectComponent)
        add(suspect.suspect_key.replace("-", " "), ACCUSE_COMMAND_TYPE, entity.id)
        add(suspect.name, ACCUSE_COMMAND_TYPE, entity.id)
    return table


def resolve_intent(world: World, text: str) -> IntentResolution:
    """Map player text to one proposed action without touching game state."""

    normalized = _normalize(text)
    if not normalized:
        return IntentResolution(status="unresolved", reason="empty request")

    command_type: str | None = None
    for candidate, verbs in _VERBS.items():
        for verb in verbs:
            if normalized == verb or normalized.startswith(f"{verb} "):
                command_type, rest = candidate, normalized[len(verb) :].strip()
                break
        if command_type is not None:
            break
    if command_type is None:
        return IntentResolution(status="unresolved", reason="no recognised action verb")

    rest = " ".join(token for token in rest.split() if token not in _FILLER).strip()
    if not rest:
        return IntentResolution(
            status="unresolved", command_type=command_type, reason="no target named"
        )

    matches: list[tuple[str, EntityId]] = []
    for phrase, entries in _targets(world).items():
        if rest != phrase and not rest.startswith(f"{phrase} "):
            continue
        matches.extend(
            (phrase, entity) for kind, entity in entries if kind == command_type
        )
    if matches:
        longest = max(len(phrase) for phrase, _entity in matches)
        matches = [(phrase, entity) for phrase, entity in matches if len(phrase) == longest]
    # Key, full name, and surname may all name the same entity.
    # Deduplicate identity, but keep distinct characters ambiguous.
    matches = list(dict.fromkeys(matches))
    if len(matches) > 1:
        return IntentResolution(
            status="unresolved", command_type=command_type, reason="ambiguous target"
        )
    if not matches:
        return IntentResolution(
            status="unresolved", command_type=command_type, reason="unknown target"
        )

    _phrase, target = matches[0]
    return IntentResolution(
        status="resolved",
        command_type=command_type,
        target_id=str(target),
        target_key=_target_key(world, target),
        topic=interview_topic(text) if command_type == TALK_COMMAND_TYPE else None,
    )


def _target_key(world: World, entity_id: EntityId) -> str:
    entity = world.get_entity(entity_id)
    if entity.has_component(ArchiveEvidenceComponent):
        return entity.get_component(ArchiveEvidenceComponent).evidence_key
    if entity.has_component(ArchiveWitnessComponent):
        return entity.get_component(ArchiveWitnessComponent).witness_key
    if entity.has_component(ArchiveSuspectComponent):
        return entity.get_component(ArchiveSuspectComponent).suspect_key
    return str(entity_id)


def perform(
    ctx: HandlerContext,
    *,
    character_id: str,
    controller_id: str,
    controller_generation: int,
    resolution: IntentResolution,
    apply: Callable[[HandlerContext, HandlerResult], object] | None = None,
    topic: str | None = None,
) -> HandlerResult | None:
    """Run a resolved proposal through the real handler. Returns None if unresolved.

    ``apply`` applies the mutation plan; the caller supplies it because only the host knows
    whether it is inside a tick or a deterministic test.
    """

    if resolution.status != "resolved" or resolution.command_type is None:
        return None
    handler = _HANDLERS[resolution.command_type]()
    command = _build_command(
        character_id=character_id,
        controller_id=controller_id,
        controller_generation=controller_generation,
        command_type=resolution.command_type,
        target_id=resolution.target_id or "",
        topic=topic if topic is not None else resolution.topic,
    )
    result = handler.execute(ctx, command)
    if result.ok and apply is not None:
        apply(ctx, result)
    return result


def _build_command(
    *,
    character_id: str,
    controller_id: str,
    controller_generation: int,
    command_type: str,
    target_id: str,
    topic: str | None = None,
) -> SubmittedCommand:
    from bunnyland.core import CommandCost, Lane, build_submitted_command

    return build_submitted_command(
        character_id=character_id,
        controller_id=controller_id,
        controller_generation=controller_generation,
        command_type=command_type,
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={"target_id": target_id, **(
            {"topic": topic} if topic is not None and command_type == TALK_COMMAND_TYPE else {}
        )},
    )


def build_packet(
    world: World,
    character_id: EntityId | str,
    result: HandlerResult | None = None,
    *,
    action: str = "",
) -> NarrationPacket:
    """Package a restricted view plus the public part of an outcome.

    Privileged event fields (``culprit_match``, ``missing_evidence``) and the sealed
    solution never cross this boundary.
    """

    if parse_entity_id(character_id) is None:
        raise ValueError("unknown investigator")
    view = narrator_view(world, character_id)
    if result is None:
        return NarrationPacket(view=view)
    return NarrationPacket(view=view, outcome=_public_outcome(result, action, view))


def _public_outcome(
    result: HandlerResult, action: str, view: ArchiveNarratorView,
) -> NarrationOutcome:
    if not result.ok:
        return NarrationOutcome(action=action, accepted=False, detail=result.reason)
    for event in result.events:
        if isinstance(event, EvidenceExaminedEvent):
            return NarrationOutcome(
                action=COMMAND_TYPE,
                accepted=True,
                observation=event.observation,
                first_discovery=event.first_discovery,
            )
        if isinstance(event, WitnessQuestionedEvent):
            return NarrationOutcome(
                action=TALK_COMMAND_TYPE,
                accepted=True,
                statements=event.statements,
                witness_key=event.witness_key,
                witness_name=next((w.name for w in view.witnesses
                                   if w.witness_key == event.witness_key), None),
                first_conversation=event.first_conversation,
                new_testimony=event.new_testimony,
                detail=("The witness's recorded account does not address that topic."
                        if not event.statements else ""),
            )
        if isinstance(event, AccusationResolvedEvent):
            return NarrationOutcome(
                action=ACCUSE_COMMAND_TYPE,
                accepted=True,
                verdict=event.verdict,
            )
    return NarrationOutcome(action=action, accepted=True)


__all__ = [
    "IntentResolution",
    "NarrationOutcome",
    "NarrationPacket",
    "build_packet",
    "perform",
    "resolve_intent",
]

