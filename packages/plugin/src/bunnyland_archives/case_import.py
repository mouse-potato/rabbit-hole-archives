"""Privileged import of an authored case into canonical ECS state.

This module is the only supported way to put canonical case facts into a world.
It is trusted in-process code: it is not reachable from the action pipeline, the
Narrator adapter, a client projection, or an MCP tool, and it must not be.

The authored ``CaseDefinition`` is an import input, never a second runtime truth.
After import the ECS holds the only authoritative copy, so gameplay code cannot
mutate a case by editing the file it came from.
"""

from __future__ import annotations

from dataclasses import dataclass

from bunnyland.core import (
    ContainmentMode,
    Contains,
    IdentityComponent,
    RoomComponent,
    spawn_entity,
)
from rabbit_hole_engine.authoring import CaseDefinition
from relics import EntityId, World

from .components import (
    ArchiveCaseComponent,
    ArchiveEventComponent,
    ArchiveEvidenceComponent,
    ArchivePlaceComponent,
    ArchiveSuspectComponent,
    EvidenceFromEvent,
    SealedSolutionComponent,
)


class CaseImportError(RuntimeError):
    """Raised when importing would corrupt or duplicate canonical state."""


@dataclass(frozen=True)
class ImportedCase:
    """Entity references produced by one import, keyed by authored identifiers."""

    case_key: str
    case_entity: EntityId
    places: dict[str, EntityId]
    events: dict[str, EntityId]
    suspects: dict[str, EntityId]
    evidence: dict[str, EntityId]


def imported_case_keys(world: World) -> frozenset[str]:
    """Return the case keys already present in canonical state."""

    return frozenset(
        entity.get_component(ArchiveCaseComponent).case_key
        for entity in world.query().with_all([ArchiveCaseComponent]).execute_entities()
    )


def import_case(world: World, case: CaseDefinition) -> ImportedCase:
    """Materialize one validated case as canonical entities.

    ``CaseDefinition`` already guarantees identifier uniqueness and reference
    integrity, so this function only enforces runtime preconditions: a case may be
    imported once per world.
    """

    if case.id in imported_case_keys(world):
        raise CaseImportError(f"case {case.id!r} is already imported")

    case_entity = spawn_entity(
        world,
        [
            ArchiveCaseComponent(
                case_key=case.id,
                case_version=case.schema_version,
                title=case.title,
                start_place_key=case.start_location,
            ),
            SealedSolutionComponent(
                culprit_key=case.solution.culprit,
                explanation=case.solution.explanation,
                supporting_evidence=case.solution.supporting_evidence,
            ),
        ],
    )

    places: dict[str, EntityId] = {}
    for location in case.locations:
        place = spawn_entity(
            world,
            [
                RoomComponent(title=location.name),
                ArchivePlaceComponent(place_key=location.id, name=location.name),
            ],
        )
        places[location.id] = place.id

    events: dict[str, EntityId] = {}
    for event in case.events:
        entity = spawn_entity(
            world,
            [ArchiveEventComponent(event_key=event.id, description=event.description)],
        )
        events[event.id] = entity.id

    suspects: dict[str, EntityId] = {}
    for suspect in case.suspects:
        entity = spawn_entity(
            world,
            [ArchiveSuspectComponent(suspect_key=suspect.id, name=suspect.name)],
        )
        suspects[suspect.id] = entity.id

    evidence: dict[str, EntityId] = {}
    for clue in case.evidence:
        entity = spawn_entity(
            world,
            [
                IdentityComponent(name=clue.id, kind="evidence"),
                ArchiveEvidenceComponent(
                    case_key=case.id,
                    evidence_key=clue.id,
                    observation=clue.observation,
                    source_event_key=clue.source_event,
                    place_key=clue.location,
                ),
            ],
        )
        world.get_entity(places[clue.location]).add_relationship(
            Contains(mode=ContainmentMode.ROOM_CONTENT), entity.id
        )
        entity.add_relationship(EvidenceFromEvent(), events[clue.source_event])
        evidence[clue.id] = entity.id

    return ImportedCase(
        case_key=case.id,
        case_entity=case_entity.id,
        places=places,
        events=events,
        suspects=suspects,
        evidence=evidence,
    )


__all__ = ["CaseImportError", "ImportedCase", "import_case", "imported_case_keys"]
