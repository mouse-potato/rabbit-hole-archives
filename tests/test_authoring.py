import json
from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError
from rabbit_hole_engine.authoring import CaseDefinition


def case_data() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "id": "missing_seal",
        "title": "The Missing Seal",
        "start_location": "study",
        "locations": [{"id": "study", "name": "Study"}],
        "events": [{"id": "theft", "description": "Ada took the seal."}],
        "suspects": [{"id": "ada", "name": "Ada"}],
        "evidence": [{"id": "receipt", "location": "study",
                      "observation": "A signed receipt for the seal: Ada.",
                      "source_event": "theft"}],
        "solution": {"culprit": "ada", "explanation": "Ada signed for the seal.",
                     "supporting_evidence": ["receipt"]},
    }


def parse(data: dict[str, Any]) -> CaseDefinition:
    return CaseDefinition.model_validate_json(json.dumps(data))


def test_valid_case_round_trip() -> None:
    case = parse(case_data())
    assert CaseDefinition.model_validate_json(case.model_dump_json()) == case
    assert case.evidence[0].source_event == "theft"


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(schema_version=2),
    lambda d: d.update(schema_version="1"),
    lambda d: d.update(unexpected="ignored?"),
    lambda d: d.update(start_location="nowhere"),
    lambda d: d.update(title="  "),
    lambda d: d["evidence"][0].update(id="study"),
    lambda d: d["evidence"][0].update(location="nowhere"),
    lambda d: d["evidence"][0].update(source_event="invented"),
    lambda d: d["evidence"][0].update(secret="extra"),
    lambda d: d["solution"].update(culprit="invented"),
    lambda d: d["solution"].update(supporting_evidence=[]),
    lambda d: d["solution"].update(supporting_evidence=["invented"]),
    lambda d: d["solution"].update(supporting_evidence=["receipt", "receipt"]),
    lambda d: d.update(evidence=[]),
    lambda d: d.update(id="../unsafe"),
])
def test_invalid_cases(mutate: Callable[[dict[str, Any]], None]) -> None:
    data = case_data()
    mutate(data)
    with pytest.raises(ValidationError):
        parse(data)


def test_unreachable_solution_support_rejected() -> None:
    data = case_data()
    data["locations"].append({"id": "attic", "name": "Attic"})
    data["evidence"][0]["location"] = "attic"
    with pytest.raises(ValidationError, match="accessible"):
        parse(data)


def test_definition_is_immutable() -> None:
    case = parse(case_data())
    with pytest.raises(ValidationError):
        case.evidence[0].observation = "Narrator invention"  # type: ignore[misc]
