"""Focused interviews grant only selected, per-investigator testimony."""
from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest
from archive_harness import (
    build_scenario,
    canonical_snapshot,
    conversation_entities,
    narrator_projection,
    save_and_reload,
    talk,
    talk_command,
)
from bunnyland.core import ContainmentMode, Contains, spawn_entity
from bunnyland.core.ecs import replace_component
from bunnyland_archives import (
    ArchiveConversationComponent,
    InvestigatorSessionComponent,
    TalkToWitnessHandler,
    apply_handler_result,
    narrator_view,
    perform,
    resolve_intent,
)
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI, public_focus_options
from pydantic import TypeAdapter


def test_focused_question_hides_unselected_statement_from_every_public_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[dict[str, Any]] = []

    def model(_self: LocalAI, _system: str, payload: dict[str, Any]) -> dict[str, str]:
        requests.append(payload)
        return {"tone": "curious", "focus": "testimony:1", "text": "INVENTED"}

    monkeypatch.setattr(LocalAI, "_ask", model)
    game = DemoGame(ai=LocalAI(model="mock"))
    result = game.act("ask Quill about receipt")
    assert len(result["view"]["heard"]) == 1
    assert "arguing" not in str(result)
    assert "arguing" not in str(requests)
    assert "arguing" not in str(public_focus_options(result))
    assert "INVENTED" not in str(result)
    remembered = game.act("what did Quill say about seal?")
    assert "does not address" in remembered["outcome"]["detail"]
    assert "arguing" not in str(remembered)
    assert "arguing" not in game.act("review casebook")["outcome"]["detail"]


def test_topics_accumulate_in_authored_order_and_repeated_topics_are_idempotent() -> None:
    game = DemoGame()
    receipt = game.act("ask Quill about receipt")
    assert len(receipt["view"]["heard"]) == 1
    seal = game.act("what about seal?")
    assert len(seal["outcome"]["statements"]) == 1
    assert len(seal["view"]["heard"]) == 2
    assert "arguing" in seal["view"]["heard"][0]["statement"]
    repeated = game.act("what about receipt?")
    assert repeated["view"] == seal["view"]
    assert repeated["outcome"]["new_testimony"] is False
    assert repeated["view"]["discovered"] == []


@pytest.mark.parametrize("topic", ["spaceship", "", "the", "everything"])
def test_unanswered_topic_grants_no_testimony_or_leads(topic: str) -> None:
    game = DemoGame()
    result = game.act("ask Quill about " + topic)
    assert result["outcome"]["accepted"]
    assert result["outcome"]["statements"] == []
    assert result["view"]["heard"] == []
    assert result["conversation"]["lead_topics"] == []
    assert result["outcome"]["new_testimony"] is False
    assert "no leads recorded" in game.act("review leads")["outcome"]["detail"]


def test_repeating_general_interview_does_not_drain_the_whole_account() -> None:
    game = DemoGame()
    first = game.act("talk to porter")
    for _ in range(3):
        again = game.act("talk to porter")
        assert again["view"] == first["view"]
        assert again["outcome"]["new_testimony"] is False
    assert len(first["view"]["heard"]) == 1
    assert first["conversation"]["lead_topics"] == []


def test_handler_scopes_topic_before_plan_and_keeps_partial_knowledge_after_reload() -> None:
    scenario = build_scenario()
    before = canonical_snapshot(scenario)
    resolution = resolve_intent(scenario.world, "ask porter about receipt")
    assert resolution.topic == "receipt"
    result = perform(
        scenario.ctx(), character_id=str(scenario.character),
        controller_id=str(scenario.controller), controller_generation=scenario.generation,
        resolution=resolution,
    )
    assert result is not None and result.ok
    assert narrator_projection(scenario).heard == ()  # uncommitted plan grants nothing
    apply_handler_result(scenario.ctx(), result)
    view = narrator_projection(scenario)
    assert len(view.heard) == 1
    assert view.heard[0].lead_evidence_key == "receipt"
    assert "raised voices" not in view.model_dump_json()
    record = conversation_entities(scenario)[0].get_component(ArchiveConversationComponent)
    assert record.testimony_keys == ("porter-saw-receipt",)
    restored = save_and_reload(scenario)
    assert narrator_projection(restored) == view
    repeat = perform(
        restored.ctx(), character_id=str(restored.character),
        controller_id=str(restored.controller), controller_generation=restored.generation,
        resolution=resolve_intent(restored.world, "ask porter about receipt"),
        apply=apply_handler_result,
    )
    assert repeat is not None and repeat.ok
    assert repeat.plan is not None and repeat.plan.operations == ()
    talk(restored, restored.imported.witnesses["porter"])
    assert len(narrator_projection(restored).heard) == 2
    assert len(conversation_entities(restored)) == 1
    assert canonical_snapshot(restored) == before


def test_partial_testimony_does_not_grant_another_investigator_knowledge() -> None:
    scenario = build_scenario()
    other = spawn_entity(scenario.world, [InvestigatorSessionComponent(case_key=scenario.case.id)])
    scenario.world.get_entity(scenario.imported.places["study"]).add_relationship(
        Contains(mode=ContainmentMode.ROOM_CONTENT), other.id,
    )
    talk(scenario, scenario.imported.witnesses["porter"])
    assert len(narrator_projection(scenario).heard) == 1
    assert narrator_view(scenario.world, other.id).heard == ()


def test_empty_knowledge_remains_empty_after_reload() -> None:
    scenario = build_scenario()
    perform(
        scenario.ctx(), character_id=str(scenario.character),
        controller_id=str(scenario.controller), controller_generation=scenario.generation,
        resolution=resolve_intent(scenario.world, "ask porter about spaceship"),
        apply=apply_handler_result,
    )
    restored = save_and_reload(scenario)
    assert narrator_projection(restored).heard == ()
    record = conversation_entities(restored)[0].get_component(ArchiveConversationComponent)
    assert record.testimony_keys == ()
    perform(
        restored.ctx(), character_id=str(restored.character),
        controller_id=str(restored.controller), controller_generation=restored.generation,
        resolution=resolve_intent(restored.world, "ask porter about receipt"),
        apply=apply_handler_result,
    )
    assert len(narrator_projection(restored).heard) == 1


def test_topic_matching_multiple_statements_has_stable_keys_on_repeat() -> None:
    scenario = build_scenario()
    before = canonical_snapshot(scenario)
    results = [perform(
        scenario.ctx(), character_id=str(scenario.character),
        controller_id=str(scenario.controller), controller_generation=scenario.generation,
        resolution=resolve_intent(scenario.world, "ask porter about receipt and voices"),
        apply=apply_handler_result,
    ) for _ in range(2)]
    assert len(narrator_projection(scenario).heard) == 2
    repeated = results[1]
    assert repeated is not None and repeated.plan is not None
    assert repeated.plan.operations == ()
    assert len(conversation_entities(scenario)) == 1
    assert canonical_snapshot(scenario) == before


def test_legacy_conversation_without_statement_keys_keeps_existing_knowledge() -> None:
    scenario = build_scenario()
    talk(scenario, scenario.imported.witnesses["porter"])
    entity = conversation_entities(scenario)[0]
    legacy = TypeAdapter(ArchiveConversationComponent).validate_python({
        "case_key": scenario.case.id, "witness_key": "porter", "first_heard_at_epoch": 0,
    })
    assert legacy.testimony_keys is None
    replace_component(entity, legacy)
    restored = save_and_reload(scenario)
    assert len(narrator_projection(restored).heard) == 2
    perform(
        restored.ctx(), character_id=str(restored.character),
        controller_id=str(restored.controller), controller_generation=restored.generation,
        resolution=resolve_intent(restored.world, "ask porter about receipt"),
        apply=apply_handler_result,
    )
    assert len(narrator_projection(restored).heard) == 2


@pytest.mark.parametrize("topic", [123, [], {}, "x" * 301])
def test_invalid_topic_payload_is_rejected_without_recording(topic: Any) -> None:
    scenario = build_scenario()
    command = talk_command(scenario, scenario.imported.witnesses["porter"])
    command = replace(command, payload={**command.payload, "topic": topic})
    result = TalkToWitnessHandler().execute(scenario.ctx(), command)
    assert not result.ok
    assert conversation_entities(scenario) == []
