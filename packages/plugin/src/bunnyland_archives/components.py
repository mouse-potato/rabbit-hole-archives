"""ECS components owned by the ``bunnyland.archives`` plugin.

Two deliberately separate groups:

* **Canonical** components describe the case as authored (places, historical
  events, suspects, evidence, sealed solution). They are written once by the
  privileged importer and are never part of a gameplay mutation plan.
* **Mutable** components describe one investigator's progress (session, discovery
  records). Only these are ever changed by action handlers.

Sealing is an authorization property of this code, not a property of ECS storage.
Anyone holding an in-process reference to the world can read every component.
"""

from __future__ import annotations

from pydantic.dataclasses import dataclass
from relics import Component, Edge


@dataclass(frozen=True)
class ArchiveCaseComponent(Component):
    """Singleton per imported case; the root of its canonical entity graph."""

    case_key: str
    case_version: int
    title: str
    start_place_key: str


@dataclass(frozen=True)
class ArchivePlaceComponent(Component):
    """A canonical location, attached to the room entity actors move through."""

    place_key: str
    name: str


@dataclass(frozen=True)
class ArchiveEventComponent(Component):
    """A sealed historical fact. Never projected to players or the Narrator."""

    event_key: str
    description: str


@dataclass(frozen=True)
class ArchiveSuspectComponent(Component):
    """A canonical suspect. Not a live character; testimony arrives in a later slice."""

    suspect_key: str
    name: str


@dataclass(frozen=True)
class ArchiveEvidenceComponent(Component):
    """A canonical, discoverable clue. The observation is the sealed canonical text."""

    case_key: str
    evidence_key: str
    observation: str
    source_event_key: str
    place_key: str


@dataclass(frozen=True)
class SealedSolutionComponent(Component):
    """The authored answer. Privileged: no player, client, or Narrator projection."""

    culprit_key: str
    explanation: str
    supporting_evidence: tuple[str, ...]


@dataclass(frozen=True)
class InvestigatorSessionComponent(Component):
    """Mutable: which imported case this character is investigating."""

    case_key: str


@dataclass(frozen=True)
class DiscoveryComponent(Component):
    """Mutable: one evidence discovery record, owned by exactly one investigator."""

    case_key: str
    evidence_key: str
    discovered_at_epoch: int


@dataclass(frozen=True)
class EvidenceFromEvent(Edge):
    """evidence -> canonical event that produced it (provenance)."""


@dataclass(frozen=True)
class DiscoveredBy(Edge):
    """discovery record -> investigator character."""


@dataclass(frozen=True)
class DiscoveryOf(Edge):
    """discovery record -> canonical evidence entity."""


CANONICAL_COMPONENTS: tuple[type, ...] = (
    ArchiveCaseComponent,
    ArchivePlaceComponent,
    ArchiveEventComponent,
    ArchiveSuspectComponent,
    ArchiveEvidenceComponent,
    SealedSolutionComponent,
)

MUTABLE_COMPONENTS: tuple[type, ...] = (
    InvestigatorSessionComponent,
    DiscoveryComponent,
)

COMPONENT_TYPES: tuple[type, ...] = (*CANONICAL_COMPONENTS, *MUTABLE_COMPONENTS)

EDGE_TYPES: tuple[type, ...] = (EvidenceFromEvent, DiscoveredBy, DiscoveryOf)
