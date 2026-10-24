"""Reused witness keys must never join testimony across imported cases."""
from __future__ import annotations

from archive_harness import (
    build_case,
    build_scenario,
    canonical_snapshot,
    case_data,
    narrator_projection,
    save_and_reload,
    talk,
)
from bunnyland_archives import import_case
from bunnyland_archives.mechanics import WitnessQuestionedEvent


def test_interview_and_projection_exclude_other_cases_before_and_after_reload() -> None:
    scenario = build_scenario()
    other = case_data()
    other["id"] = "other_case"
    for statement in other["testimony"]:
        statement["statement"] = "PRIVATE_OTHER_CASE_TESTIMONY"
    import_case(scenario.world, build_case(other))
    before = canonical_snapshot(scenario)

    assert narrator_projection(scenario).heard == ()
    result = talk(scenario, scenario.imported.witnesses["porter"])
    event = next(e for e in result.events if isinstance(e, WitnessQuestionedEvent))
    assert len(event.statements) == 1
    assert "PRIVATE_OTHER_CASE_TESTIMONY" not in str(event.statements)
    view = narrator_projection(scenario)
    assert len(view.heard) == 1
    assert "PRIVATE_OTHER_CASE_TESTIMONY" not in view.model_dump_json()
    assert canonical_snapshot(scenario) == before

    restored = save_and_reload(scenario)
    assert narrator_projection(restored) == view
    repeated = talk(restored, restored.imported.witnesses["porter"])
    assert "PRIVATE_OTHER_CASE_TESTIMONY" not in str(repeated.events)
    assert canonical_snapshot(restored) == before
