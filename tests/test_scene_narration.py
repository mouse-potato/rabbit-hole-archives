"""Authored scene-aware Narrator beats preserve canonical mystery boundaries."""
from __future__ import annotations

from typing import Any

import pytest
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI, trusted_narration


@pytest.mark.parametrize(("command", "expected"), [
    ("examine receipt", "study's paperwork"),
    ("talk to porter", "quiet study"),
    ("go to hall", "side door"),
])
def test_offline_action_gets_scene_specific_narration(
    command: str, expected: str,
) -> None:
    game = DemoGame()
    result = game.act(command)
    assert result["outcome"]["accepted"] is True
    assert expected in result["narration"]
    assert "narration" not in game.packet()


def test_scene_changes_narration_without_exposing_next_clue() -> None:
    game = DemoGame()
    game.act("go to hall")
    result = game.act("look at glove")
    assert "Near the side door" in result["narration"]
    assert "Ada signed the seal out and concealed it" not in str(result)
    assert result["outcome"]["observation"].startswith("Inside a damp riding glove")


def test_model_cannot_smuggle_text_into_scene_beat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ai = LocalAI(model="mock")
    def malicious(
        _self: LocalAI, _system: str, _payload: dict[str, Any],
    ) -> dict[str, str]:
        return {"tone": "tense", "text": "The murderer is SEALED_SECRET"}

    monkeypatch.setattr(LocalAI, "_ask", malicious)
    game = DemoGame(ai=ai)
    result = game.act("examine receipt")
    assert "The details demand careful scrutiny." in result["narration"]
    assert "study's paperwork" in result["narration"]
    assert "SEALED_SECRET" not in str(result)


def test_denied_action_never_receives_misleading_scene_beat() -> None:
    game = DemoGame()
    result = game.act("examine glove")
    assert result["outcome"]["accepted"] is False
    assert result["narration"] == "That action cannot be completed."


def test_unknown_action_narration_uses_reviewed_fallback() -> None:
    packet: dict[str, Any] = {
        "view": {"place_key": "study"},
        "outcome": {"action": "something_unknown", "accepted": True},
    }
    assert trusted_narration(packet, "curious") == "You consider what you have learned."
