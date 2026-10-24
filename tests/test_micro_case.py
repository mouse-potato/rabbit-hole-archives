"""Slice 4: a playable micro-case - witnesses, attributed testimony, leads, accusation.

Everything here is deterministic: no model calls, no narration, no autonomous ticks.
"""

from __future__ import annotations

import json

import pytest
from archive_harness import (
    accusation_entities,
    accuse,
    build_case,
    build_scenario,
    canonical_snapshot,
    case_data,
    conversation_entities,
    discovery_entities,
    examine,
    move_to,
    narrator_projection,
    save_and_reload,
    talk,
)
from pydantic import ValidationError
from rabbit_hole_engine.authoring import CaseDefinition, resolve_accusation


def parse(data: dict[str, object]) -> CaseDefinition:
    return CaseDefinition.model_validate_json(json.dumps(data))


# -- schema ----------------------------------------------------------------------


def test_witness_case_round_trips() -> None:
    case = build_case()

    assert [witness.id for witness in case.witnesses] == ["porter", "maid"]
    assert case.testimony[1].points_to == "receipt"
    assert CaseDefinition.model_validate_json(case.model_dump_json()) == case


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["witnesses"][0].update(location="nowhere"),
        lambda d: d["witnesses"][0].update(id="receipt"),
        lambda d: d["testimony"][0].update(witness="nobody"),
        lambda d: d["testimony"][0].update(points_to="invented"),
        lambda d: d["testimony"][1].update(id=d["testimony"][0]["id"]),
        lambda d: d.update(testimony=[{"id": "x", "witness": "porter", "statement": "  "}]),
    ],
)
def test_invalid_witness_data_is_rejected(mutate) -> None:  # type: ignore[no-untyped-def]
    data = case_data()
    mutate(data)

    with pytest.raises(ValidationError):
        parse(data)


def test_version_one_cases_cannot_carry_witnesses() -> None:
    data = case_data()
    data["schema_version"] = 1

    with pytest.raises(ValidationError):
        parse(data)


# -- accusation resolution -------------------------------------------------------


def test_correct_accusation_with_support_is_solved() -> None:
    case = build_case()

    outcome = resolve_accusation(
        suspect_id="ada",
        culprit=case.solution.culprit,
        supporting_evidence=case.solution.supporting_evidence,
        discovered_evidence=("receipt",),
    )

    assert outcome.verdict == "solved"
    assert outcome.culprit_match is True
    assert outcome.missing_evidence == ()


def test_correct_suspect_without_support_stays_unproven() -> None:
    case = build_case()

    outcome = resolve_accusation(
        suspect_id="ada",
        culprit=case.solution.culprit,
        supporting_evidence=case.solution.supporting_evidence,
        discovered_evidence=(),
    )

    assert outcome.verdict == "unproven"
    assert outcome.culprit_match is True  # privileged bookkeeping only
    assert outcome.missing_evidence == ("receipt",)


def test_wrong_suspect_is_unproven() -> None:
    case = build_case()

    outcome = resolve_accusation(
        suspect_id="porter",
        culprit=case.solution.culprit,
        supporting_evidence=case.solution.supporting_evidence,
        discovered_evidence=("receipt",),
    )

    assert outcome.verdict == "unproven"
    assert outcome.culprit_match is False
    assert outcome.missing_evidence == ()


# -- import ----------------------------------------------------------------------


def test_witnesses_are_imported_into_their_canonical_rooms() -> None:
    scenario = build_scenario()

    assert scenario.room_of(scenario.imported.witnesses["porter"]) == scenario.imported.places[
        "study"
    ]
    assert scenario.room_of(scenario.imported.witnesses["maid"]) == scenario.imported.places["hall"]
    assert set(scenario.imported.testimony) == {
        "porter-heard-arguing",
        "porter-saw-receipt",
        "maid-saw-glove",
    }


# -- testimony -------------------------------------------------------------------


def test_questioning_returns_attributed_statements_in_authored_order() -> None:
    scenario = build_scenario()

    result = talk(scenario, scenario.imported.witnesses["porter"])

    assert result.ok
    event = result.events[0]
    assert event.witness_key == "porter"  # type: ignore[attr-defined]
    assert event.statements == (  # type: ignore[attr-defined]
        "I heard raised voices in the study before the seal went missing.",
    )
    assert event.leads == ()  # type: ignore[attr-defined]
    assert event.first_conversation is True  # type: ignore[attr-defined]


def test_questioning_records_one_conversation() -> None:
    scenario = build_scenario()

    talk(scenario, scenario.imported.witnesses["porter"])
    talk(scenario, scenario.imported.witnesses["porter"])

    assert len(conversation_entities(scenario)) == 1


def test_repeat_questioning_is_idempotent_and_keeps_the_same_text() -> None:
    scenario = build_scenario()
    first = talk(scenario, scenario.imported.witnesses["porter"])

    again = talk(scenario, scenario.imported.witnesses["porter"])

    assert again.ok
    assert again.events[0].statements == first.events[0].statements  # type: ignore[attr-defined]
    assert again.events[0].first_conversation is False  # type: ignore[attr-defined]
    assert len(conversation_entities(scenario)) == 1


def test_witness_out_of_reach_cannot_be_questioned() -> None:
    scenario = build_scenario()

    result = talk(scenario, scenario.imported.witnesses["maid"])

    assert not result.ok
    assert "not here" in result.reason
    assert conversation_entities(scenario) == []


def test_moving_then_questioning_works() -> None:
    scenario = build_scenario()
    move_to(scenario, "hall")

    result = talk(scenario, scenario.imported.witnesses["maid"])

    assert result.ok
    assert result.events[0].leads == ("glove",)  # type: ignore[attr-defined]


def test_only_witnesses_can_be_questioned() -> None:
    scenario = build_scenario()

    result = talk(scenario, scenario.imported.evidence["receipt"])

    assert not result.ok
    assert "not a witness" in result.reason


# -- accusation ------------------------------------------------------------------


def test_accusing_a_non_suspect_is_rejected() -> None:
    scenario = build_scenario()

    result = accuse(scenario, scenario.imported.witnesses["porter"])

    assert not result.ok
    assert "not a suspect" in result.reason
    assert accusation_entities(scenario) == []


def test_accusation_without_support_is_unproven_and_recorded() -> None:
    scenario = build_scenario()

    result = accuse(scenario, scenario.imported.suspects["ada"])

    assert result.ok
    event = result.events[0]
    assert event.verdict == "unproven"  # type: ignore[attr-defined]
    assert event.culprit_match is True  # type: ignore[attr-defined]
    assert event.missing_evidence == ("receipt",)  # type: ignore[attr-defined]
    assert len(accusation_entities(scenario)) == 1
    assert narrator_projection(scenario).solved is False


def test_accusation_with_support_solves_the_case() -> None:
    scenario = build_scenario()
    examine(scenario, scenario.imported.evidence["receipt"])

    result = accuse(scenario, scenario.imported.suspects["ada"])

    assert result.events[0].verdict == "solved"  # type: ignore[attr-defined]
    assert narrator_projection(scenario).solved is True


def test_public_view_does_not_distinguish_wrong_suspect_from_thin_case() -> None:
    wrong = build_scenario()  # innocent suspect, all evidence in hand
    thin = build_scenario()  # right suspect, no supporting evidence
    examine(wrong, wrong.imported.evidence["receipt"])

    wrong_result = accuse(wrong, wrong.imported.suspects["halloran"])
    thin_result = accuse(thin, thin.imported.suspects["ada"])

    # Only the privileged events differ; the public projection exposes one boolean.
    assert wrong_result.events[0].culprit_match is False  # type: ignore[attr-defined]
    assert thin_result.events[0].culprit_match is True  # type: ignore[attr-defined]
    assert wrong_result.events[0].verdict == "unproven"  # type: ignore[attr-defined]
    assert thin_result.events[0].verdict == "unproven"  # type: ignore[attr-defined]
    assert narrator_projection(wrong).solved is narrator_projection(thin).solved is False


# -- immutability and projection -------------------------------------------------


def test_canonical_state_is_unchanged_by_questioning_and_accusation() -> None:
    scenario = build_scenario()
    before = canonical_snapshot(scenario)

    talk(scenario, scenario.imported.witnesses["porter"])
    examine(scenario, scenario.imported.evidence["receipt"])
    accuse(scenario, scenario.imported.suspects["ada"])

    assert canonical_snapshot(scenario) == before


def test_projection_lists_only_witnesses_actually_present() -> None:
    scenario = build_scenario()

    view = narrator_projection(scenario)

    assert [witness.witness_key for witness in view.witnesses] == ["porter"]
    assert view.heard == ()


def test_unheard_testimony_never_reaches_the_projection() -> None:
    scenario = build_scenario()

    payload = narrator_projection(scenario).model_dump_json()

    assert "raised voices" not in payload
    assert "did not come back for it" not in payload


def test_only_opening_testimony_reaches_the_projection() -> None:
    scenario = build_scenario()
    talk(scenario, scenario.imported.witnesses["porter"])

    view = narrator_projection(scenario)

    assert [item.witness_key for item in view.heard] == ["porter"]
    assert [item.lead_evidence_key for item in view.heard] == [None]
    assert "receipt on the desk" not in view.model_dump_json()
    assert "did not come back for it" not in view.model_dump_json()


def test_investigation_state_survives_save_and_reload() -> None:
    scenario = build_scenario()
    talk(scenario, scenario.imported.witnesses["porter"])
    examine(scenario, scenario.imported.evidence["receipt"])
    accuse(scenario, scenario.imported.suspects["ada"])
    before = narrator_projection(scenario)

    reloaded = save_and_reload(scenario)

    assert len(conversation_entities(reloaded)) == 1
    assert len(accusation_entities(reloaded)) == 1
    assert len(discovery_entities(reloaded)) == 1
    assert narrator_projection(reloaded) == before
    assert before.solved is True

