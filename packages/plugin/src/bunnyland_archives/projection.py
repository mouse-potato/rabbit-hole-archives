"""Restricted projections for the Narrator and clients.

Everything here is derived from mutable, per-character state. A projection may
include an observation only after that investigator recorded it, and it never
includes sealed solution facts, historical event text, or unexamined evidence.

Deliberately absent: the solution component, event descriptions, and any component
owned by a clue the investigator has not examined.
"""

from __future__ import annotations

from bunnyland.core import IdentityComponent, container_of, parse_entity_id
from pydantic import BaseModel, ConfigDict
from relics import Entity, EntityId, World

from .components import (
    ArchiveCaseComponent,
    ArchiveEvidenceComponent,
    ArchivePlaceComponent,
    DiscoveredBy,
    DiscoveryComponent,
    DiscoveryOf,
    InvestigatorSessionComponent,
)


class ProjectionError(LookupError):
    """Raised when a character has no archive session to project."""


class DiscoveredEvidenceView(BaseModel):
    """One clue the investigator has already examined."""

    model_config = ConfigDict(frozen=True)

    evidence_key: str
    label: str
    observation: str


class ArchiveNarratorView(BaseModel):
    """The complete, safe archive state available to narration for one character."""

    model_config = ConfigDict(frozen=True)

    case_key: str
    case_title: str
    place_key: str | None
    place_name: str | None
    discovered: tuple[DiscoveredEvidenceView, ...]


def _case_entity(world: World, case_key: str) -> Entity:
    for entity in world.query().with_all([ArchiveCaseComponent]).execute_entities():
        if entity.get_component(ArchiveCaseComponent).case_key == case_key:
            return entity
    raise ProjectionError(f"case {case_key!r} is not loaded")


def narrator_view(world: World, character_id: EntityId | str) -> ArchiveNarratorView:
    """Project only what this investigator has legitimately discovered."""

    parsed = parse_entity_id(character_id)
    if parsed is None or not world.has_entity(parsed):
        raise ProjectionError("unknown investigator")
    character = world.get_entity(parsed)
    if not character.has_component(InvestigatorSessionComponent):
        raise ProjectionError("character has no archive session")

    case_key = character.get_component(InvestigatorSessionComponent).case_key
    case = _case_entity(world, case_key).get_component(ArchiveCaseComponent)

    place_key: str | None = None
    place_name: str | None = None
    room_id = container_of(character)
    if room_id is not None and world.has_entity(room_id):
        room = world.get_entity(room_id)
        if room.has_component(ArchivePlaceComponent):
            place = room.get_component(ArchivePlaceComponent)
            place_key = place.place_key
            place_name = place.name

    discovered: list[DiscoveredEvidenceView] = []
    for record_entity in world.query().with_all([DiscoveryComponent]).execute_entities():
        record = record_entity.get_component(DiscoveryComponent)
        if record.case_key != case_key:
            continue
        if not record_entity.has_relationship(DiscoveredBy, parsed):
            continue
        for _edge, evidence_id in record_entity.get_relationships(DiscoveryOf):
            if not world.has_entity(evidence_id):
                continue
            evidence_entity = world.get_entity(evidence_id)
            if not evidence_entity.has_component(ArchiveEvidenceComponent):
                continue
            evidence = evidence_entity.get_component(ArchiveEvidenceComponent)
            label = evidence.evidence_key
            if evidence_entity.has_component(IdentityComponent):
                label = evidence_entity.get_component(IdentityComponent).name
            discovered.append(
                DiscoveredEvidenceView(
                    evidence_key=evidence.evidence_key,
                    label=label,
                    observation=evidence.observation,
                )
            )
    discovered.sort(key=lambda item: item.evidence_key)

    return ArchiveNarratorView(
        case_key=case.case_key,
        case_title=case.title,
        place_key=place_key,
        place_name=place_name,
        discovered=tuple(discovered),
    )


__all__ = [
    "ArchiveNarratorView",
    "DiscoveredEvidenceView",
    "ProjectionError",
    "narrator_view",
]
