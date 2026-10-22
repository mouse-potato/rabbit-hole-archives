"""Deterministic examination of canonical evidence through Bunnyland actions.

The handler reads canonical facts and writes only mutable discovery state. It never
emits a mutation that targets a canonical component, and it returns the authored
observation verbatim so repeated runs produce identical results.
"""

from __future__ import annotations

from bunnyland.core import (
    AddEdge,
    AddEntity,
    DomainEvent,
    EntityReference,
    EventVisibility,
    HandlerContext,
    HandlerResult,
    MutationPlan,
    SubmittedCommand,
    execute_mutation_plan,
    parse_entity_id,
    reachable_ids,
)
from bunnyland.core.handlers.base import planned, rejected
from rabbit_hole_engine.authoring import resolve_accusation
from relics import Entity, EntityId

from .actions import ACCUSE_SUSPECT, TALK_TO_WITNESS
from .components import (
    AccusationBy,
    AccusationOf,
    ArchiveAccusationComponent,
    ArchiveCaseComponent,
    ArchiveConversationComponent,
    ArchiveEvidenceComponent,
    ArchiveSuspectComponent,
    ArchiveTestimonyComponent,
    ArchiveWitnessComponent,
    ConversationBy,
    ConversationWith,
    DiscoveredBy,
    DiscoveryComponent,
    DiscoveryOf,
    InvestigatorSessionComponent,
    SealedSolutionComponent,
)

COMMAND_TYPE = "examine-evidence"
TALK_COMMAND_TYPE = TALK_TO_WITNESS.command_type
ACCUSE_COMMAND_TYPE = ACCUSE_SUSPECT.command_type


class EvidenceExaminedEvent(DomainEvent):
    """One deterministic examination outcome, including the canonical observation."""

    character_id: str
    evidence_id: str
    evidence_key: str
    observation: str
    first_discovery: bool


def _target_id(command: SubmittedCommand) -> object | None:
    payload = command.payload
    if "target_id" in payload:
        return payload["target_id"]
    return payload.get("evidence_id")


def _existing_discovery(
    ctx: HandlerContext,
    *,
    case_key: str,
    evidence_key: str,
    character_id: EntityId,
) -> Entity | None:
    for entity in ctx.world.query().with_all([DiscoveryComponent]).execute_entities():
        record = entity.get_component(DiscoveryComponent)
        if record.case_key != case_key or record.evidence_key != evidence_key:
            continue
        if entity.has_relationship(DiscoveredBy, character_id):
            return entity
    return None


class ExamineEvidenceHandler:
    """Reach a clue, return its canonical observation, record one discovery."""

    command_type = COMMAND_TYPE

    def can_handle(self, ctx: HandlerContext, command: SubmittedCommand) -> bool:
        raw_target = _target_id(command)
        if raw_target is None:
            return False
        target_id = parse_entity_id(raw_target)
        if target_id is None or not ctx.world.has_entity(target_id):
            return True
        character_id = parse_entity_id(command.character_id)
        if character_id is None or not ctx.world.has_entity(character_id):
            return True
        if target_id not in reachable_ids(ctx.world, ctx.entity(character_id)):
            return True
        return bool(ctx.entity(target_id).has_component(ArchiveEvidenceComponent))

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        character_id = parse_entity_id(command.character_id)
        if character_id is None or not ctx.world.has_entity(character_id):
            return rejected("invalid character id")
        target_id = parse_entity_id(_target_id(command))
        if target_id is None or not ctx.world.has_entity(target_id):
            return rejected("there is nothing like that to examine")
        evidence_entity = ctx.entity(target_id)
        if not evidence_entity.has_component(ArchiveEvidenceComponent):
            return rejected("that is not case evidence")
        if target_id not in reachable_ids(ctx.world, ctx.entity(character_id)):
            return rejected("you cannot examine that from here")

        evidence = evidence_entity.get_component(ArchiveEvidenceComponent)
        recorded = _existing_discovery(
            ctx,
            case_key=evidence.case_key,
            evidence_key=evidence.evidence_key,
            character_id=character_id,
        )
        event = EvidenceExaminedEvent(
            **ctx.event_base(
                visibility=EventVisibility.PRIVATE,
                actor_id=str(character_id),
                room_id=None,
                target_ids=(str(target_id),),
                character_id=str(character_id),
                evidence_id=str(target_id),
                evidence_key=evidence.evidence_key,
                observation=evidence.observation,
                first_discovery=recorded is None,
            )
        )
        if recorded is not None:
            # Idempotent: same canonical text, no new casebook record, no mutation.
            return planned(MutationPlan(), event)

        reference = EntityReference()
        return planned(
            MutationPlan(
                (
                    AddEntity(
                        components=(
                            DiscoveryComponent(
                                case_key=evidence.case_key,
                                evidence_key=evidence.evidence_key,
                                discovered_at_epoch=ctx.epoch,
                            ),
                        ),
                        reference=reference,
                    ),
                    AddEdge(
                        source_id=reference,
                        target_id=character_id,
                        edge=DiscoveredBy(),
                    ),
                    AddEdge(
                        source_id=reference,
                        target_id=target_id,
                        edge=DiscoveryOf(),
                    ),
                )
            ),
            event,
        )


def apply_handler_result(
    ctx: HandlerContext,
    result: HandlerResult,
) -> tuple[DomainEvent, ...]:
    """Apply a handler plan and return the events that were published.

    Bunnyland's actor does this inside a tick. Deterministic tests and privileged
    import tooling use this helper instead of driving the asynchronous actor loop.
    """

    if not result.ok:
        return ()
    if result.plan is None:
        return result.events
    _summary, deferred = execute_mutation_plan(
        ctx.world,
        result.plan,
        after_apply=lambda: tuple(factory() for factory in result.event_factories),
    )
    return (*result.events, *deferred)


__all__ = [
    "ACCUSE_COMMAND_TYPE",
    "COMMAND_TYPE",
    "TALK_COMMAND_TYPE",
    "AccusationResolvedEvent",
    "AccuseSuspectHandler",
    "EvidenceExaminedEvent",
    "ExamineEvidenceHandler",
    "TalkToWitnessHandler",
    "WitnessQuestionedEvent",
    "apply_handler_result",
    "discovered_evidence_keys",
]


class WitnessQuestionedEvent(DomainEvent):
    """One deterministic interrogation outcome: attributed statements and their leads."""

    character_id: str
    witness_id: str
    witness_key: str
    statements: tuple[str, ...]
    leads: tuple[str, ...]
    first_conversation: bool


class AccusationResolvedEvent(DomainEvent):
    """One deterministic accusation outcome.

    ``culprit_match`` and ``missing_evidence`` are privileged bookkeeping. Public narration
    must use ``verdict`` only, so a wrong accusation cannot reveal the right suspect.
    """

    character_id: str
    suspect_id: str
    suspect_key: str
    verdict: str
    culprit_match: bool
    missing_evidence: tuple[str, ...]


def _testimony_for(
    ctx: HandlerContext, case_key: str, witness_key: str,
) -> list[ArchiveTestimonyComponent]:
    statements = [
        entity.get_component(ArchiveTestimonyComponent)
        for entity in ctx.world.query()
        .with_all([ArchiveTestimonyComponent])
        .execute_entities()
    ]
    return sorted(
        (item for item in statements
         if item.case_key == case_key and item.witness_key == witness_key),
        key=lambda item: item.order,
    )


def _existing_conversation(
    ctx: HandlerContext,
    *,
    case_key: str,
    witness_key: str,
    character_id: EntityId,
) -> Entity | None:
    for entity in ctx.world.query().with_all([ArchiveConversationComponent]).execute_entities():
        record = entity.get_component(ArchiveConversationComponent)
        if record.case_key != case_key or record.witness_key != witness_key:
            continue
        if entity.has_relationship(ConversationBy, character_id):
            return entity
    return None


def _sealed_solution(
    ctx: HandlerContext,
    case_key: str,
) -> SealedSolutionComponent | None:
    for entity in ctx.world.query().with_all([ArchiveCaseComponent]).execute_entities():
        if entity.get_component(ArchiveCaseComponent).case_key != case_key:
            continue
        if entity.has_component(SealedSolutionComponent):
            return entity.get_component(SealedSolutionComponent)
    return None


def discovered_evidence_keys(
    ctx: HandlerContext,
    *,
    case_key: str,
    character_id: EntityId,
) -> tuple[str, ...]:
    """Return the evidence keys this investigator has already recorded."""

    keys: list[str] = []
    for entity in ctx.world.query().with_all([DiscoveryComponent]).execute_entities():
        record = entity.get_component(DiscoveryComponent)
        if record.case_key != case_key:
            continue
        if entity.has_relationship(DiscoveredBy, character_id):
            keys.append(record.evidence_key)
    return tuple(sorted(set(keys)))


class TalkToWitnessHandler:
    """Hear a witness out, in authored order, and record one conversation."""

    command_type = TALK_COMMAND_TYPE

    def can_handle(self, ctx: HandlerContext, command: SubmittedCommand) -> bool:
        raw_target = _target_id(command)
        if raw_target is None:
            return False
        target_id = parse_entity_id(raw_target)
        if target_id is None or not ctx.world.has_entity(target_id):
            return True
        character_id = parse_entity_id(command.character_id)
        if character_id is None or not ctx.world.has_entity(character_id):
            return True
        if target_id not in reachable_ids(ctx.world, ctx.entity(character_id)):
            return True
        return bool(ctx.entity(target_id).has_component(ArchiveWitnessComponent))

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        character_id = parse_entity_id(command.character_id)
        if character_id is None or not ctx.world.has_entity(character_id):
            return rejected("invalid character id")
        target_id = parse_entity_id(_target_id(command))
        if target_id is None or not ctx.world.has_entity(target_id):
            return rejected("there is no one like that to question")
        witness_entity = ctx.entity(target_id)
        if not witness_entity.has_component(ArchiveWitnessComponent):
            return rejected("that is not a witness in this case")
        if target_id not in reachable_ids(ctx.world, ctx.entity(character_id)):
            return rejected("they are not here to question")
        character = ctx.entity(character_id)
        if not character.has_component(InvestigatorSessionComponent):
            return rejected("you are not investigating a case")

        witness = witness_entity.get_component(ArchiveWitnessComponent)
        session = character.get_component(InvestigatorSessionComponent)
        if session.case_key != witness.case_key:
            return rejected("that witness belongs to a different case")

        statements = _testimony_for(ctx, witness.case_key, witness.witness_key)
        recorded = _existing_conversation(
            ctx,
            case_key=witness.case_key,
            witness_key=witness.witness_key,
            character_id=character_id,
        )
        event = WitnessQuestionedEvent(
            **ctx.event_base(
                visibility=EventVisibility.PRIVATE,
                actor_id=str(character_id),
                room_id=None,
                target_ids=(str(target_id),),
                character_id=str(character_id),
                witness_id=str(target_id),
                witness_key=witness.witness_key,
                statements=tuple(item.statement for item in statements),
                leads=tuple(
                    item.points_to_key for item in statements if item.points_to_key is not None
                ),
                first_conversation=recorded is None,
            )
        )
        if recorded is not None:
            return planned(MutationPlan(), event)

        reference = EntityReference()
        return planned(
            MutationPlan(
                (
                    AddEntity(
                        components=(
                            ArchiveConversationComponent(
                                case_key=witness.case_key,
                                witness_key=witness.witness_key,
                                first_heard_at_epoch=ctx.epoch,
                            ),
                        ),
                        reference=reference,
                    ),
                    AddEdge(
                        source_id=reference,
                        target_id=character_id,
                        edge=ConversationBy(),
                    ),
                    AddEdge(
                        source_id=reference,
                        target_id=target_id,
                        edge=ConversationWith(),
                    ),
                )
            ),
            event,
        )


class AccuseSuspectHandler:
    """Resolve an accusation against the sealed solution and the investigator's evidence."""

    command_type = ACCUSE_COMMAND_TYPE

    def can_handle(self, ctx: HandlerContext, command: SubmittedCommand) -> bool:
        raw_target = _target_id(command)
        if raw_target is None:
            return False
        target_id = parse_entity_id(raw_target)
        if target_id is None or not ctx.world.has_entity(target_id):
            return True
        return bool(ctx.entity(target_id).has_component(ArchiveSuspectComponent))

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        character_id = parse_entity_id(command.character_id)
        if character_id is None or not ctx.world.has_entity(character_id):
            return rejected("invalid character id")
        target_id = parse_entity_id(_target_id(command))
        if target_id is None or not ctx.world.has_entity(target_id):
            return rejected("there is no such suspect to accuse")
        suspect_entity = ctx.entity(target_id)
        if not suspect_entity.has_component(ArchiveSuspectComponent):
            return rejected("that is not a suspect in this case")
        character = ctx.entity(character_id)
        if not character.has_component(InvestigatorSessionComponent):
            return rejected("you are not investigating a case")

        case_key = character.get_component(InvestigatorSessionComponent).case_key
        suspect = suspect_entity.get_component(ArchiveSuspectComponent)
        solution = _sealed_solution(ctx, case_key)
        if solution is None:  # pragma: no cover - import always writes the case root
            return rejected("the case record is missing")
        discovered = discovered_evidence_keys(
            ctx, case_key=case_key, character_id=character_id
        )
        outcome = resolve_accusation(
            suspect_id=suspect.suspect_key,
            culprit=solution.culprit_key,
            supporting_evidence=solution.supporting_evidence,
            discovered_evidence=discovered,
        )

        event = AccusationResolvedEvent(
            **ctx.event_base(
                visibility=EventVisibility.PRIVATE,
                actor_id=str(character_id),
                room_id=None,
                target_ids=(str(target_id),),
                character_id=str(character_id),
                suspect_id=str(target_id),
                suspect_key=suspect.suspect_key,
                verdict=outcome.verdict,
                culprit_match=outcome.culprit_match,
                missing_evidence=outcome.missing_evidence,
            )
        )
        reference = EntityReference()
        return planned(
            MutationPlan(
                (
                    AddEntity(
                        components=(
                            ArchiveAccusationComponent(
                                case_key=case_key,
                                suspect_key=suspect.suspect_key,
                                verdict=outcome.verdict,
                                culprit_match=outcome.culprit_match,
                                missing_evidence=outcome.missing_evidence,
                                made_at_epoch=ctx.epoch,
                            ),
                        ),
                        reference=reference,
                    ),
                    AddEdge(
                        source_id=reference,
                        target_id=character_id,
                        edge=AccusationBy(),
                    ),
                    AddEdge(
                        source_id=reference,
                        target_id=target_id,
                        edge=AccusationOf(),
                    ),
                )
            ),
            event,
        )


