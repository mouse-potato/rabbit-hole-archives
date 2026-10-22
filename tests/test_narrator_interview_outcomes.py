"""Narration acknowledges the actual outcome and the attributed topic only."""
from __future__ import annotations

from typing import Any

import pytest
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI, public_focus_options


def test_first_and_repeated_interviews_have_public_speaker_and_history() -> None:
    game = DemoGame()
    first = game.act("talk to porter")
    again = game.act("what about receipt?")
    for result in (first, again):
        assert result["outcome"]["witness_key"] == "porter"
        assert result["outcome"]["witness_name"] == "Porter Quill"
        assert "Porter Quill" in result["narration"]
    assert first["outcome"]["first_conversation"] is True
    assert again["outcome"]["first_conversation"] is False
    assert "learn another part" in again["narration"]
    assert first["outcome"]["new_testimony"] is True
    assert again["outcome"]["new_testimony"] is True
    assert len(first["view"]["heard"]) == 1
    assert len(again["view"]["heard"]) == 2
    repeated = game.act("what about receipt?")
    assert repeated["outcome"]["new_testimony"] is False
    assert "recorded account" in repeated["narration"]
    assert repeated["view"] == again["view"]


def test_unknown_topic_narration_does_not_claim_an_answer() -> None:
    result = DemoGame().act("ask Quill about the spaceship")
    assert "offers no answer" in result["narration"]
    assert "Porter Quill" in result["narration"]
    assert not any(key.startswith("testimony:") for key in public_focus_options(result))


def test_interview_focus_is_scoped_to_speaker_and_selected_topic() -> None:
    game = DemoGame()
    game.act("talk to porter")
    game.act("go to hall")
    game.act("talk to maid")
    game.act("examine glove")
    game.act("go to study")
    result = game.act("ask Quill about receipt")
    choices = public_focus_options(result)
    assert "witness:porter" in choices
    assert "witness:maid" not in choices
    assert not any(key.startswith("clue:") for key in choices)
    assert "desk receipt" in str(choices)
    assert "arguing" not in str(choices)
    assert "riding gloves" not in str(choices)


def test_model_cannot_restore_off_topic_statement(monkeypatch: pytest.MonkeyPatch) -> None:
    payloads: list[dict[str, Any]] = []

    def model(_self: LocalAI, _system: str, payload: dict[str, Any]) -> dict[str, str]:
        payloads.append(payload)
        return {"tone": "curious", "focus": "testimony:0", "text": "INVENTED_DIALOGUE"}

    monkeypatch.setattr(LocalAI, "_ask", model)
    game = DemoGame(ai=LocalAI(model="mock"))
    result = game.act("ask Quill about receipt")
    assert "arguing" not in result["narration"]
    assert "INVENTED_DIALOGUE" not in result["narration"]
    choices = payloads[-1]["focus_options"]
    assert isinstance(choices, dict)
    assert "desk receipt" in str(choices)
    assert "arguing" not in str(choices)
    assert "Ada carried the seal" not in str(payloads)


def test_rejected_interview_does_not_publish_unavailable_speaker() -> None:
    result = DemoGame().act("talk to maid")
    assert not result["outcome"]["accepted"]
    assert result["outcome"]["witness_name"] is None
    assert result["outcome"]["first_conversation"] is None
