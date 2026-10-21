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
    """A canonical suspect. Not a live character; no autonomous behaviour."""

    suspect_key: str
    name: str


@dataclass(frozen=True)
class ArchiveWitnessComponent(Component):
    """A canonical witness, placed in one canonical room so travel governs access."""

    case_key: str
    witness_key: str
    name: str
    place_key: str


@dataclass(frozen=True)
class ArchiveTestimonyComponent(Component):
    """One sealed, attributed statement in authored order.

    ``points_to_key`` is a lead (an evidence key), never the clue's observation, so
    revealing a lead cannot reveal what the clue says.
    """

    case_key: str
    testimony_key: str
    witness_key: str
    statement: str
    points_to_key: str | None
    order: int


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
class ArchiveConversationComponent(Component):
    """Mutable: one record that an investigator has heard a witness out."""

    case_key: str
    witness_key: str
    first_heard_at_epoch: int


@dataclass(frozen=True)
class ArchiveAccusationComponent(Component):
    """Mutable: one accusation an investigator has formally made.

    ``verdict`` and ``culprit_match`` are privileged bookkeeping. Player-facing text never
    distinguishes "wrong person" from "not enough evidence".
    """

    case_key: str
    suspect_key: str
    verdict: str
    culprit_match: bool
    missing_evidence: tuple[str, ...]
    made_at_epoch: int


@dataclass(frozen=True)
class EvidenceFromEvent(Edge):
    """evidence -> canonical event that produced it (provenance)."""


@dataclass(frozen=True)
class TestimonyFromWitness(Edge):
    """testimony -> canonical witness who said it (attribution)."""


@dataclass(frozen=True)
class TestimonyPointsTo(Edge):
    """testimony -> canonical evidence it leads toward."""


@dataclass(frozen=True)
class DiscoveredBy(Edge):
    """discovery record -> investigator character."""


@dataclass(frozen=True)
class DiscoveryOf(Edge):
    """discovery record -> canonical evidence entity."""


@dataclass(frozen=True)
class ConversationBy(Edge):
    """conversation record -> investigator character."""


@dataclass(frozen=True)
class ConversationWith(Edge):
    """conversation record -> canonical witness entity."""


@dataclass(frozen=True)
class AccusationBy(Edge):
    """accusation record -> investigator character."""


@dataclass(frozen=True)
class AccusationOf(Edge):
    """accusation record -> canonical suspect entity."""


CANONICAL_COMPONENTS: tuple[type, ...] = (
    ArchiveCaseComponent,
    ArchivePlaceComponent,
    ArchiveEventComponent,
    ArchiveSuspectComponent,
    ArchiveEvidenceComponent,
    ArchiveWitnessComponent,
    ArchiveTestimonyComponent,
    SealedSolutionComponent,
)

MUTABLE_COMPONENTS: tuple[type, ...] = (
    InvestigatorSessionComponent,
    DiscoveryComponent,
    ArchiveConversationComponent,
    ArchiveAccusationComponent,
)

COMPONENT_TYPES: tuple[type, ...] = (*CANONICAL_COMPONENTS, *MUTABLE_COMPONENTS)

EDGE_TYPES: tuple[type, ...] = (
    EvidenceFromEvent,
    TestimonyFromWitness,
    TestimonyPointsTo,
    DiscoveredBy,
    DiscoveryOf,
    ConversationBy,
    ConversationWith,
    AccusationBy,
    AccusationOf,
)
