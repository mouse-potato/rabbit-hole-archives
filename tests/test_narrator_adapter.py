"""Slice 5 (core): non-authoritative Narrator adapter and deterministic intent parsing."""

from __future__ import annotations

import json

from archive_harness import (
    accuse,
    build_case,
    build_scenario,
    case_data,
    discovery_entities,
    examine,
    narrator_projection,
    talk,
)
from bunnyland_archives import (
    ACCUSE_COMMAND_TYPE,
    COMMAND_TYPE,
    TALK_COMMAND_TYPE,
    apply_handler_result,
    build_packet,
    perform,
    resolve_intent,
)


def resolve(scenario, text: str):  # type: ignore[no-untyped-def]
    return resolve_intent(scenario.world, text)


# -- intent parsing is deterministic and side-effect free ------------------------


def test_examine_intent_resolves_to_evidence() -> None:
    scenario = build_scenario()

    resolution = resolve(scenario, "Examine the receipt, please.")

    assert resolution.status == "resolved"
    assert resolution.command_type == COMMAND_TYPE
    assert resolution.target_key == "receipt"


def test_talk_intent_resolves_by_key_or_name() -> None:
    scenario = build_scenario()

    by_key = resolve(scenario, "talk to porter")
    by_name = resolve(scenario, "question Maid Rosalind")

    assert (by_key.command_type, by_key.target_key) == (TALK_COMMAND_TYPE, "porter")
    assert (by_name.command_type, by_name.target_key) == (TALK_COMMAND_TYPE, "maid")


def test_accuse_intent_resolves_to_a_suspect() -> None:
    scenario = build_scenario()

    resolution = resolve(scenario, "accuse Ada Vance")

    assert resolution.command_type == ACCUSE_COMMAND_TYPE
    assert resolution.target_key == "ada"


def test_intent_parsing_changes_nothing() -> None:
    scenario = build_scenario()

    resolve(scenario, "examine the receipt")
    resolve(scenario, "accuse ada")

    assert discovery_entities(scenario) == []
    assert narrator_projection(scenario).solved is False


def test_unknown_verbs_and_targets_stay_unresolved() -> None:
    scenario = build_scenario()

    assert resolve(scenario, "dance wildly").reason == "no recognised action verb"
    assert resolve(scenario, "examine").reason == "no target named"
    assert resolve(scenario, "examine the moon").status == "unresolved"
    assert resolve(scenario, "examine the moon").reason == "unknown target"


def test_ambiguous_names_are_refused_rather_than_guessed() -> None:
    data = case_data()
    data["witnesses"].append({"id": "porter2", "name": "Porter Quill", "location": "study"})
    scenario = build_scenario(build_case(data))

    resolution = resolve(scenario, "talk to Porter Quill")

    assert resolution.status == "unresolved"
    assert resolution.reason == "ambiguous target"


# -- performing a proposal -------------------------------------------------------


def test_perform_runs_the_real_handler_without_applying_by_default() -> None:
    scenario = build_scenario()

    result = perform(
        scenario.ctx(),
        character_id=str(scenario.character),
        controller_id=str(scenario.controller),
        controller_generation=scenario.generation,
        resolution=resolve(scenario, "examine receipt"),
    )

    assert result is not None and result.ok
    assert discovery_entities(scenario) == []  # caller decides when to apply


def test_perform_with_apply_records_the_discovery() -> None:
    scenario = build_scenario()

    result = perform(
        scenario.ctx(),
        character_id=str(scenario.character),
        controller_id=str(scenario.controller),
        controller_generation=scenario.generation,
        resolution=resolve(scenario, "examine receipt"),
        apply=apply_handler_result,
    )

    assert result is not None and result.ok
    assert len(discovery_entities(scenario)) == 1


def test_unresolved_intent_performs_nothing() -> None:
    scenario = build_scenario()

    result = perform(
        scenario.ctx(),
        character_id=str(scenario.character),
        controller_id=str(scenario.controller),
        controller_generation=scenario.generation,
        resolution=resolve(scenario, "dance wildly"),
    )

    assert result is None


# -- narration packets stay inside the boundary ----------------------------------


def test_packet_contains_only_the_restricted_view() -> None:
    scenario = build_scenario()
    examine(scenario, scenario.imported.evidence["receipt"])

    packet = build_packet(scenario.world, scenario.character)

    assert packet.view == narrator_projection(scenario)
    assert "carried it out" not in packet.model_dump_json()


def test_examination_packet_carries_the_observation() -> None:
    scenario = build_scenario()

    result = perform(
        scenario.ctx(),
        character_id=str(scenario.character),
        controller_id=str(scenario.controller),
        controller_generation=scenario.generation,
        resolution=resolve(scenario, "examine receipt"),
        apply=apply_handler_result,
    )
    packet = build_packet(
        scenario.world, scenario.character, result, action=COMMAND_TYPE
    )

    assert packet.outcome is not None
    assert packet.outcome.observation == "A signed receipt for the seal, in Ada's hand."
    assert packet.outcome.action == COMMAND_TYPE


def test_testimony_packet_carries_statements_but_not_sealed_text() -> None:
    scenario = build_scenario()
    result = talk(scenario, scenario.imported.witnesses["porter"])

    packet = build_packet(
        scenario.world, scenario.character, result, action=TALK_COMMAND_TYPE
    )

    assert packet.outcome is not None
    assert packet.outcome.statements[0].startswith("I heard raised voices")
    assert "Ada signed for the seal" not in packet.model_dump_json()


def test_accusation_packet_exposes_only_the_public_verdict() -> None:
    scenario = build_scenario()
    result = accuse(scenario, scenario.imported.suspects["ada"])

    packet = build_packet(
        scenario.world, scenario.character, result, action=ACCUSE_COMMAND_TYPE
    )

    assert packet.outcome is not None
    assert packet.outcome.verdict == "unproven"
    payload = packet.model_dump_json()
    assert "culprit_match" not in payload
    assert "missing_evidence" not in payload
    assert "receipt" not in json.dumps(packet.outcome.model_dump())


def test_rejected_action_packet_reports_a_reason_only() -> None:
    scenario = build_scenario()

    result = perform(
        scenario.ctx(),
        character_id=str(scenario.character),
        controller_id=str(scenario.controller),
        controller_generation=scenario.generation,
        resolution=resolve(scenario, "talk to maid"),  # maid is in the other room
    )
    packet = build_packet(
        scenario.world, scenario.character, result, action=TALK_COMMAND_TYPE
    )

    assert packet.outcome is not None
    assert packet.outcome.accepted is False
    assert packet.outcome.detail == "they are not here to question"
    assert packet.outcome.statements == ()
