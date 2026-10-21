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
from relics import Entity, EntityId

from .components import (
    ArchiveEvidenceComponent,
    DiscoveredBy,
    DiscoveryComponent,
    DiscoveryOf,
)

COMMAND_TYPE = "examine-evidence"


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
    "COMMAND_TYPE",
    "EvidenceExaminedEvent",
    "ExamineEvidenceHandler",
    "apply_handler_result",
]
