"""M1 ECS-boundary proof for the archive plugin against real Bunnyland.

Covers the slice-2 acceptance points: privileged import, deterministic examination
through an action handler, inaccessible/duplicate behavior, canonical immutability,
and a restricted Narrator projection. No model calls or autonomous ticks.
"""

from __future__ import annotations

import asyncio

import pytest
from archive_harness import (
    build_case,
    build_scenario,
    canonical_snapshot,
    case_data,
    discovery_entities,
    examine,
    examine_command,
    move_to,
    narrator_projection,
)
from bunnyland.core import IdentityComponent, RoomComponent
from bunnyland.core.world_actor import SubmissionOutcome
from bunnyland.plugins import PluginRegistry
from bunnyland_archives import (
    COMMAND_TYPE,
    PLUGIN_ID,
    ArchiveCaseComponent,
    ArchiveEvidenceComponent,
    ArchiveNarratorView,
    CaseImportError,
    DiscoveryComponent,
    SealedSolutionComponent,
    archive_plugin,
    import_case,
    imported_case_keys,
)

# -- plugin wiring -----------------------------------------------------------------


def test_plugin_applies_through_the_real_loader() -> None:
    scenario = build_scenario()
    plugin = archive_plugin()

    assert plugin.id == PLUGIN_ID
    assert COMMAND_TYPE in scenario.actor.available_command_types()
    definitions = {item.command_type: item for item in scenario.actor.action_definitions()}
    assert definitions[COMMAND_TYPE].tool_name == "examine_evidence"
    assert any(
        component is ArchiveEvidenceComponent for component in plugin.ecs.components
    )
    assert any(component is SealedSolutionComponent for component in plugin.ecs.components)
    assert isinstance(scenario.actor.plugins, PluginRegistry)


def test_plugin_exports_are_registered_with_owner() -> None:
    registry = PluginRegistry([archive_plugin()])

    assert registry.components["ArchiveEvidenceComponent"][0] == PLUGIN_ID
    assert registry.events[(PLUGIN_ID, "EvidenceExaminedEvent")] is not None


def test_submission_validation_accepts_the_real_action() -> None:
    """Proves the action survives Bunnyland's own submission chokepoint."""

    scenario = build_scenario()
    outcome: SubmissionOutcome = asyncio.run(
        scenario.actor.submit(examine_command(scenario, scenario.imported.evidence["receipt"]))
    )

    assert outcome.accepted, outcome.reason


# -- privileged import -------------------------------------------------------------


def test_import_materializes_canonical_entities_per_room() -> None:
    scenario = build_scenario()

    assert imported_case_keys(scenario.world) == {"missing_seal"}
    receipt = scenario.world.get_entity(scenario.imported.evidence["receipt"])
    assert receipt.get_component(ArchiveEvidenceComponent).place_key == "study"
    assert receipt.has_component(IdentityComponent)
    study = scenario.world.get_entity(scenario.imported.places["study"])
    assert study.has_component(RoomComponent)
    assert study.get_component(RoomComponent).title == "The Study"


def test_import_refuses_a_duplicate_case() -> None:
    scenario = build_scenario()

    with pytest.raises(CaseImportError):
        import_case(scenario.world, build_case())


def test_imported_case_keeps_a_single_sealed_solution() -> None:
    scenario = build_scenario()
    solutions = [
        entity
        for entity in scenario.world.query().with_all([SealedSolutionComponent]).execute_entities()
    ]

    assert len(solutions) == 1
    sealed = solutions[0].get_component(SealedSolutionComponent)
    assert sealed.culprit_key == "ada"


# -- deterministic examination -----------------------------------------------------


def test_examination_returns_the_same_canonical_observation_every_run() -> None:
    observations = []
    for _ in range(3):
        scenario = build_scenario()
        result = examine(scenario, scenario.imported.evidence["receipt"])
        assert result.ok
        assert len(result.events) == 1
        observations.append(result.events[0].observation)  # type: ignore[attr-defined]

    assert observations == [
        "A signed receipt for the seal, in Ada's hand.",
    ] * 3


def test_first_examination_records_one_discovery() -> None:
    scenario = build_scenario()

    result = examine(scenario, scenario.imported.evidence["receipt"])

    assert result.ok
    assert result.events[0].first_discovery is True  # type: ignore[attr-defined]
    records = discovery_entities(scenario)
    assert len(records) == 1
    record = records[0].get_component(DiscoveryComponent)
    assert record.evidence_key == "receipt"
    assert record.case_key == "missing_seal"


def test_duplicate_examination_is_idempotent() -> None:
    scenario = build_scenario()
    first = examine(scenario, scenario.imported.evidence["receipt"])
    second = examine(scenario, scenario.imported.evidence["receipt"])

    assert first.ok and second.ok
    assert second.events[0].first_discovery is False  # type: ignore[attr-defined]
    assert second.events[0].observation == first.events[0].observation  # type: ignore[attr-defined]
    assert second.plan is not None and second.plan.operations == ()
    assert len(discovery_entities(scenario)) == 1


def test_inaccessible_evidence_is_rejected_and_records_nothing() -> None:
    scenario = build_scenario()
    move_to(scenario, "hall")

    result = examine(scenario, scenario.imported.evidence["receipt"])

    assert not result.ok
    assert result.reason == "you cannot examine that from here"
    assert discovery_entities(scenario) == []


def test_reachable_evidence_in_another_room_can_be_examined_after_moving() -> None:
    scenario = build_scenario()
    move_to(scenario, "hall")

    result = examine(scenario, scenario.imported.evidence["glove"])

    assert result.ok
    assert result.events[0].observation == "A single glove, still damp."  # type: ignore[attr-defined]


def test_non_evidence_and_unknown_targets_are_rejected() -> None:
    scenario = build_scenario()
    room = scenario.imported.places["study"]
    unknown = "00000000-0000-0000-0000-000000000000"

    room_result = examine(scenario, room)
    unknown_result = examine(scenario, unknown)

    assert not room_result.ok
    assert room_result.reason == "that is not case evidence"
    assert not unknown_result.ok
    assert unknown_result.reason == "there is nothing like that to examine"
    assert discovery_entities(scenario) == []


# -- canonical immutability --------------------------------------------------------


def test_canonical_components_are_unchanged_by_gameplay() -> None:
    scenario = build_scenario()
    before = canonical_snapshot(scenario)

    examine(scenario, scenario.imported.evidence["receipt"])
    examine(scenario, scenario.imported.evidence["receipt"])
    move_to(scenario, "hall")
    examine(scenario, scenario.imported.evidence["glove"])

    assert canonical_snapshot(scenario) == before


def test_gameplay_writes_only_mutable_discovery_state() -> None:
    scenario = build_scenario()
    before = canonical_snapshot(scenario)

    examine(scenario, scenario.imported.evidence["receipt"])

    added = set(canonical_snapshot(scenario)) - set(before)
    assert added == set()
    case_root = scenario.world.get_entity(scenario.imported.case_entity)
    assert case_root.has_component(ArchiveCaseComponent)


# -- restricted projection ---------------------------------------------------------


def test_projection_is_empty_before_discovery() -> None:
    scenario = build_scenario()

    view = narrator_projection(scenario)

    assert view.case_key == "missing_seal"
    assert view.discovered == ()
    assert view.place_key == "study"


def test_projection_excludes_sealed_facts_and_undiscovered_evidence() -> None:
    scenario = build_scenario()
    examine(scenario, scenario.imported.evidence["receipt"])

    payload = narrator_projection(scenario).model_dump_json()

    assert "signed receipt" in payload
    assert "single glove" not in payload  # undiscovered evidence stays hidden
    assert "Ada signed for the seal at the desk." not in payload  # sealed event text
    assert "carried it out" not in payload  # sealed solution explanation
    assert set(ArchiveNarratorView.model_fields) == {
        "case_key",
        "case_title",
        "place_key",
        "place_name",
        "discovered",
        "witnesses",
        "heard",
        "solved",
    }


def test_projection_includes_each_discovery_once() -> None:
    scenario = build_scenario()
    examine(scenario, scenario.imported.evidence["receipt"])
    examine(scenario, scenario.imported.evidence["receipt"])
    move_to(scenario, "hall")
    examine(scenario, scenario.imported.evidence["glove"])

    view = narrator_projection(scenario)

    assert [item.evidence_key for item in view.discovered] == ["glove", "receipt"]


def test_case_data_used_by_tests_is_valid() -> None:
    case = build_case(case_data())
    assert case.solution.supporting_evidence == ("receipt",)
