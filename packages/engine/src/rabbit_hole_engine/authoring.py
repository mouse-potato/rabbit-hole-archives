"""Strict authoring schema, not a runtime case store or player projection.

Solution and event objects are privileged input. Never pass a CaseDefinition to
an untrusted client or narrator. Successful validation checks graph integrity
and declared clue accessibility, not whether a human can deduce the solution.
"""

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


class Solution(AuthoredModel):
    culprit: Identifier
    explanation: Text
    supporting_evidence: tuple[Identifier, ...] = Field(min_length=1)


class CaseDefinition(AuthoredModel):
    schema_version: Literal[1]
    id: Identifier
    title: Text
    start_location: Identifier
    locations: tuple[Location, ...] = Field(min_length=1)
    events: tuple[HistoricalEvent, ...] = Field(min_length=1)
    suspects: tuple[Suspect, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    solution: Solution

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        groups = (self.locations, self.events, self.suspects, self.evidence)
        ids = [item.id for group in groups for item in group]
        if len(ids) != len(set(ids)):
            raise ValueError("entity IDs must be globally unique")
        locations = {item.id for item in self.locations}
        events = {item.id for item in self.events}
        suspects = {item.id for item in self.suspects}
        clues = {item.id for item in self.evidence}
        if self.start_location not in locations:
            raise ValueError("unknown start location")
        for clue in self.evidence:
            if clue.location not in locations:
                raise ValueError("unknown evidence location")
            if clue.source_event not in events:
                raise ValueError("unknown evidence provenance event")
        if self.solution.culprit not in suspects:
            raise ValueError("unknown culprit")
        support = self.solution.supporting_evidence
        if len(support) != len(set(support)):
            raise ValueError("duplicate solution support")
        if not set(support) <= clues:
            raise ValueError("unknown supporting evidence")
        # The first slice has no travel/gating mechanics. Do not silently declare
        # clues in other rooms reachable before those mechanics exist.
        local_clues = {item.id for item in self.evidence if item.location == self.start_location}
        if not set(support) <= local_clues:
            raise ValueError("solution support must be accessible in the first-slice room")
        return self
