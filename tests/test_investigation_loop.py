"""Repeatable authored-case playthrough with public help and lead review."""
from __future__ import annotations

import pytest
from bunnyland_archives.components import CANONICAL_COMPONENTS
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI


def canonical_facts(game: DemoGame) -> list[tuple[str, str]]:
    return sorted(
        (component.__name__, repr(entity.get_component(component)))
        for entity in game.actor.world.query().execute_entities()
        for component in CANONICAL_COMPONENTS if entity.has_component(component)
    )


def test_help_and_lead_review_are_read_only_and_do_not_call_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        pytest.fail("read-only help reached model")

    monkeypatch.setattr(LocalAI, "_ask", fail)
    game = DemoGame(ai=LocalAI(model="mock"))
    before = game.packet()
    result = game.act("help")
    assert "examine receipt" in result["outcome"]["detail"]
    assert "talk to porter" in result["outcome"]["detail"]
    assert "talk to maid" not in result["outcome"]["detail"]
    assert "examine glove" not in result["outcome"]["detail"]
    assert result["view"] == before["view"]
    leads = game.act("review leads")
    assert "no leads recorded" in leads["outcome"]["detail"]
    assert leads["view"] == before["view"]


def test_lead_review_uses_only_heard_keys_and_discovery_status() -> None:
    game = DemoGame()
    game.act("ask Quill about receipt")
    before = game.packet()
    leads = game.act("review leads")
    assert "receipt (from porter): available to examine here" in leads["outcome"]["detail"]
    assert "glove" not in leads["outcome"]["detail"]
    assert "signed" not in leads["outcome"]["detail"]
    assert leads["view"] == before["view"]
    game.act("examine receipt")
    assert "receipt (from porter): examined" in game.act("review leads")["outcome"]["detail"]
    game.act("go to hall")
    game.act("talk to maid")
    game.act("go to study")
    result = game.act("review leads")
    assert "glove (from maid): not available to examine here" in result["outcome"]["detail"]
    assert "torn velvet thread" not in result["outcome"]["detail"]


@pytest.mark.parametrize("with_model", [False, True])
def test_complete_investigation_and_restart_preserve_authored_facts(
    with_model: bool, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(LocalAI, "_ask", lambda *_args: {
        "tone": "curious", "focus": "testimony:0", "text": "INVENTED_SOLUTION",
    })
    ai = LocalAI(model="mock") if with_model else None
    game = DemoGame(ai=ai)
    canonical = canonical_facts(game)
    initial = game.packet()["view"]
    commands = [
        "help", "review leads", "talk to porter", "what about receipt?",
        "examine receipt", "examine receipt", "accuse ada", "accuse halloran",
        "go to hall", "what about receipt?", "talk to maid",
        "what about glove?", "review leads", "examine glove", "accuse ada",
    ]
    for command in commands:
        result = game.act(command)
        assert canonical_facts(game) == canonical
        serialized = str(result)
        for forbidden in ("culprit_match", "missing_evidence", "supporting_evidence",
                          "INVENTED_SOLUTION", "Ada carried the seal away concealed"):
            assert forbidden not in serialized
    assert result["view"]["solved"]
    assert result["outcome"]["verdict"] == "solved"
    assert not game.act("examine glove")["outcome"]["accepted"]
    previous_world = game.actor.world
    restarted = game.act("restart investigation")
    assert restarted["outcome"]["accepted"]
    assert game.actor.world is not previous_world
    assert canonical_facts(game) == canonical
    assert restarted["view"] == initial
    assert restarted["conversation"] is None
    assert game.ai is ai
    assert not game.act("what about receipt?")["outcome"]["accepted"]
    assert game.act("talk to porter")["outcome"]["first_conversation"] is True
    assert game.act("examine receipt")["outcome"]["first_discovery"] is True


def test_new_investigation_also_resets_an_unfinished_run() -> None:
    game = DemoGame()
    game.act("talk to porter")
    game.act("examine receipt")
    restarted = game.act("new investigation")
    assert restarted["view"]["heard"] == []
    assert restarted["view"]["discovered"] == []
    assert restarted["conversation"] is None
    assert restarted["view"]["place_key"] == "study"
