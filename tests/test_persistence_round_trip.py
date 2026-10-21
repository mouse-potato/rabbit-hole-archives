"""Slice 3: persistence round-trip and adversarial leakage checks.

Uses Bunnyland's own ``save_world``/``load_world``. There is deliberately no parallel
serializer here: if the engine cannot round-trip our components, that is the finding.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from archive_harness import (
    build_scenario,
    canonical_snapshot,
    discovery_entities,
    examine,
    move_to,
    narrator_projection,
    save_and_reload,
)
from bunnyland.core import container_of
from bunnyland.persistence import WorldMeta, load_world, save_world
from bunnyland.plugins import PluginRegistry
from bunnyland_archives import (
    PLUGIN_ID,
    ArchiveEvidenceComponent,
    DiscoveredBy,
    DiscoveryComponent,
    DiscoveryOf,
    EvidenceFromEvent,
    SealedSolutionComponent,
    imported_case_keys,
)

# -- canonical state survives a round-trip -----------------------------------------


def test_canonical_state_round_trips_identically() -> None:
    scenario = build_scenario()
    before = canonical_snapshot(scenario)

    reloaded = save_and_reload(scenario)

    assert canonical_snapshot(reloaded) == before
    assert imported_case_keys(reloaded.world) == {"missing_seal"}


def test_evidence_provenance_survives_reload() -> None:
    scenario = build_scenario()
    reloaded = save_and_reload(scenario)
    receipt = reloaded.world.get_entity(reloaded.imported.evidence["receipt"])
    event_id = reloaded.imported.events["theft"]

    assert receipt.get_component(ArchiveEvidenceComponent).source_event_key == "theft"
    assert [target for _edge, target in receipt.get_relationships(EvidenceFromEvent)] == [
        event_id
    ]


# -- discovery state survives a round-trip ----------------------------------------


def test_discoveries_round_trip_with_stable_references() -> None:
    scenario = build_scenario()
    examine(scenario, scenario.imported.evidence["receipt"])

    reloaded = save_and_reload(scenario)

    records = discovery_entities(reloaded)
    assert len(records) == 1
    record = records[0].get_component(DiscoveryComponent)
    assert record.evidence_key == "receipt"
    assert records[0].has_relationship(DiscoveredBy, reloaded.character)
    assert [target for _edge, target in records[0].get_relationships(DiscoveryOf)] == [
        reloaded.imported.evidence["receipt"]
    ]


def test_investigator_location_round_trips() -> None:
    scenario = build_scenario()
    move_to(scenario, "hall")

    reloaded = save_and_reload(scenario)

    room = container_of(reloaded.world.get_entity(reloaded.character))
    assert room == reloaded.imported.places["hall"]


def test_reexamination_after_reload_does_not_duplicate() -> None:
    scenario = build_scenario()
    examine(scenario, scenario.imported.evidence["receipt"])
    reloaded = save_and_reload(scenario)

    result = examine(reloaded, reloaded.imported.evidence["receipt"])

    assert result.ok
    assert result.events[0].first_discovery is False  # type: ignore[attr-defined]
    assert len(discovery_entities(reloaded)) == 1


def test_new_discovery_after_reload_is_recorded_once() -> None:
    scenario = build_scenario()
    examine(scenario, scenario.imported.evidence["receipt"])
    reloaded = save_and_reload(scenario)
    move_to(reloaded, "hall")

    examine(reloaded, reloaded.imported.evidence["glove"])
    examine(reloaded, reloaded.imported.evidence["glove"])

    keys = sorted(
        entity.get_component(DiscoveryComponent).evidence_key
        for entity in discovery_entities(reloaded)
    )
    assert keys == ["glove", "receipt"]


# -- projection after reload -------------------------------------------------------


def test_projection_is_unchanged_after_reload() -> None:
    scenario = build_scenario()
    examine(scenario, scenario.imported.evidence["receipt"])
    before = narrator_projection(scenario)

    reloaded = save_and_reload(scenario)

    assert narrator_projection(reloaded) == before


def test_projection_after_reload_still_hides_sealed_and_undiscovered_facts() -> None:
    scenario = build_scenario()
    examine(scenario, scenario.imported.evidence["receipt"])

    payload = narrator_projection(save_and_reload(scenario)).model_dump_json()

    assert "signed receipt" in payload
    assert "single glove" not in payload
    assert "Ada signed for the seal at the desk." not in payload
    assert "carried it out" not in payload


# -- the save file is a privileged artifact ---------------------------------------


def test_save_file_contains_sealed_facts_so_it_is_not_player_data() -> None:
    """Documents the boundary: ECS snapshots hold the solution, projections do not."""

    scenario = build_scenario()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "world.json"
        save_world(scenario.actor, path, meta=WorldMeta(plugins=(PLUGIN_ID,)))
        raw = path.read_text()

    assert "carried it out" in raw  # sealed solution explanation is in the snapshot
    assert "Ada signed for the seal at the desk." in raw  # sealed event text too
    assert "carried it out" not in narrator_projection(scenario).model_dump_json()


def test_reload_requires_the_archive_plugin() -> None:
    scenario = build_scenario()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "world.json"
        save_world(scenario.actor, path, meta=WorldMeta(plugins=(PLUGIN_ID,)))

        try:
            load_world(path, registry=PluginRegistry([]))
        except Exception as exc:  # noqa: BLE001 - asserting failure mode, not type
            assert "missing plugin" in str(exc)
        else:  # pragma: no cover - the assertion above is the point
            raise AssertionError("loading without the archive plugin should fail")


def test_sealed_solution_is_present_but_only_on_the_case_root() -> None:
    scenario = build_scenario()
    reloaded = save_and_reload(scenario)

    carriers = [
        entity
        for entity in reloaded.world.query().with_all([SealedSolutionComponent]).execute_entities()
    ]

    assert [entity.id for entity in carriers] == [reloaded.imported.case_entity]
