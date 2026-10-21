"""Strict authoring schema, not a runtime case store or player projection.

Solution and event objects are privileged input. Never pass a CaseDefinition to
an untrusted client or narrator. Successful validation checks graph integrity
and declared clue accessibility, not whether a human can deduce the solution.

Schema versions: 1 = evidence only; 2 adds witnesses, attributed testimony, and
leads (a statement may point at one clue).
"""

from collections.abc import Iterable
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]*$", max_length=80)]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AuthoredModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Location(AuthoredModel):
    id: Identifier
    name: Text


class HistoricalEvent(AuthoredModel):
    id: Identifier
    description: Text


class Suspect(AuthoredModel):
    id: Identifier
    name: Text


class Evidence(AuthoredModel):
    id: Identifier
    location: Identifier
    observation: Text
    source_event: Identifier


class Witness(AuthoredModel):
    id: Identifier
    name: Text
    location: Identifier


class Testimony(AuthoredModel):
    """One attributed statement. ``points_to`` is a lead, never the clue text."""

    id: Identifier
    witness: Identifier
    statement: Text
    points_to: Identifier | None = None


class Solution(AuthoredModel):
    culprit: Identifier
    explanation: Text
    supporting_evidence: tuple[Identifier, ...] = Field(min_length=1)


class CaseDefinition(AuthoredModel):
    schema_version: Literal[1, 2]
    id: Identifier
    title: Text
    start_location: Identifier
    locations: tuple[Location, ...] = Field(min_length=1)
    events: tuple[HistoricalEvent, ...] = Field(min_length=1)
    suspects: tuple[Suspect, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    witnesses: tuple[Witness, ...] = ()
    testimony: tuple[Testimony, ...] = ()
    solution: Solution

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        if self.schema_version == 1 and (self.witnesses or self.testimony):
            raise ValueError("witnesses and testimony require schema_version 2")
        groups = (
            self.locations,
            self.events,
            self.suspects,
            self.evidence,
            self.witnesses,
        )
        ids = [item.id for group in groups for item in group]
        if len(ids) != len(set(ids)):
            raise ValueError("entity IDs must be globally unique")
        locations = {item.id for item in self.locations}
        events = {item.id for item in self.events}
        suspects = {item.id for item in self.suspects}
        clues = {item.id for item in self.evidence}
        witnesses = {item.id for item in self.witnesses}
        statement_ids = [item.id for item in self.testimony]
        if len(statement_ids) != len(set(statement_ids)):
            raise ValueError("testimony IDs must be unique")
        if self.start_location not in locations:
            raise ValueError("unknown start location")
        for clue in self.evidence:
            if clue.location not in locations:
                raise ValueError("unknown evidence location")
            if clue.source_event not in events:
                raise ValueError("unknown evidence provenance event")
        for witness in self.witnesses:
            if witness.location not in locations:
                raise ValueError("unknown witness location")
        for statement in self.testimony:
            if statement.witness not in witnesses:
                raise ValueError("unknown testimony witness")
            if statement.points_to is not None and statement.points_to not in clues:
                raise ValueError("testimony points at unknown evidence")
        if self.solution.culprit not in suspects:
            raise ValueError("unknown culprit")
        support = self.solution.supporting_evidence
        if len(support) != len(set(support)):
            raise ValueError("duplicate solution support")
        if not set(support) <= clues:
            raise ValueError("unknown supporting evidence")
        # Legacy one-room cases had no travel mechanism. Schema v2 cases are
        # investigated across rooms; every referenced clue location is validated
        # above, while actual travel/reachability belongs to the runtime.
        if self.schema_version == 1:
            local_clues = {
                item.id for item in self.evidence if item.location == self.start_location
            }
            if not set(support) <= local_clues:
                raise ValueError("solution support must be accessible in the first-slice room")
        return self


Verdict = Literal["solved", "unproven"]


class AccusationResult(AuthoredModel):
    """Deterministic outcome of an accusation.

    ``culprit_match`` and ``missing_evidence`` are privileged debugging fields. Player-facing
    text must not distinguish "wrong person" from "under-evidenced", or a wrong guess would
    tell the player they had the right suspect.
    """

    verdict: Verdict
    culprit_match: bool
    missing_evidence: tuple[Identifier, ...] = ()


def resolve_accusation(
    *,
    suspect_id: str,
    culprit: str,
    supporting_evidence: tuple[str, ...],
    discovered_evidence: Iterable[str],
) -> AccusationResult:
    """Decide an accusation from canonical solution facts and recorded discoveries.

    Callers pass values read from the runtime truth (ECS), never an authoring file, and are
    responsible for rejecting suspects the case does not contain.
    """

    discovered = set(discovered_evidence)
    missing = tuple(
        support for support in supporting_evidence if support not in discovered
    )
    culprit_match = suspect_id == culprit
    verdict: Verdict = "solved" if culprit_match and not missing else "unproven"
    return AccusationResult(
        verdict=verdict,
        culprit_match=culprit_match,
        missing_evidence=missing,
    )
