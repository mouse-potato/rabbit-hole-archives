"""Follow-ups refer only to an explicitly interviewed witness still present."""
from __future__ import annotations

import pytest
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI


@pytest.mark.parametrize("text", [
    "what about the receipt?", "how about receipt?",
    "tell me more about the receipt", "ask him about the receipt",
])
def test_followup_reuses_active_witness_and_only_authored_statements(text: str) -> None:
    game = DemoGame()
    game.act("talk to porter")
    before = game.packet()
    result = game.act(text)
    assert result["outcome"]["accepted"]
    assert len(result["outcome"]["statements"]) == 1
    assert "desk receipt" in result["outcome"]["statements"][0]
    assert result["view"] == before["view"]
    assert result["conversation"] == {
        "witness_key": "porter", "name": "Porter Quill", "lead_topics": ["receipt"],
    }


def test_unknown_followup_has_no_invented_testimony_or_discovery() -> None:
    game = DemoGame()
    game.act("talk to porter")
    before = game.packet()
    result = game.act("what about the spaceship?")
    assert result["outcome"]["statements"] == []
    assert result["view"] == before["view"]


def test_followup_without_context_never_calls_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        pytest.fail("ambiguous follow-up reached inference")

    monkeypatch.setattr(LocalAI, "_ask", fail)
    game = DemoGame(ai=LocalAI(model="mock"))
    before = game.packet()
    result = game.act("what about the glove?")
    assert not result["outcome"]["accepted"]
    assert "Name a witness" in result["outcome"]["detail"]
    assert result["view"] == before["view"]


def test_movement_clears_context_and_next_interview_sets_new_witness() -> None:
    game = DemoGame()
    game.act("talk to porter")
    assert game.act("go to study")["conversation"]["witness_key"] == "porter"
    assert game.act("go to hall")["conversation"] is None
    assert not game.act("ask him about receipt")["outcome"]["accepted"]
    result = game.act("talk to maid")
    assert result["conversation"]["witness_key"] == "maid"
    assert result["conversation"]["lead_topics"] == ["glove"]
    assert "riding gloves" in game.act("what about the glove?")["outcome"]["statements"][0]


def test_end_conversation_clears_context_without_changing_investigation() -> None:
    game = DemoGame()
    game.act("talk to porter")
    before = game.packet()
    result = game.act("end conversation")
    assert result["conversation"] is None
    assert result["view"] == before["view"]
    assert not game.act("what about receipt")["outcome"]["accepted"]


def test_failed_interview_does_not_retain_previous_addressee() -> None:
    game = DemoGame()
    game.act("talk to porter")
    result = game.act("talk to maid")
    assert not result["outcome"]["accepted"]
    assert result["conversation"] is None
