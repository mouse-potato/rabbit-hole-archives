"""Player-described interview demeanor is cosmetic and never changes testimony."""
from __future__ import annotations

from typing import Any

import pytest
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI, approach_cue


@pytest.mark.parametrize(("phrase", "cue"), [
    ("I carefully ask Quill what he heard", "You choose your words with care."),
    ("I ask Quill softly", "You keep your voice gentle."),
    ("I firmly ask Quill for his account", "You make the question plain and direct."),
])
def test_approach_is_reflected_in_interview_narration(
    phrase: str, cue: str,
) -> None:
    game = DemoGame()
    result = game.act(phrase)
    assert result["outcome"]["accepted"] is True
    assert result["narration"].startswith(cue)
    assert len(result["view"]["heard"]) == 1


def test_approach_is_cosmetic_and_cannot_create_testimony() -> None:
    calm = DemoGame()
    firm = DemoGame()
    a = calm.act("I softly ask Quill what he heard")
    b = firm.act("I sternly ask Quill what he heard")
    assert a["outcome"]["statements"] == b["outcome"]["statements"]
    assert a["view"]["heard"] == b["view"]["heard"]
    assert a["view"]["discovered"] == b["view"]["discovered"] == []


def test_approach_does_not_change_evidence_actions() -> None:
    game = DemoGame()
    response = game.act("carefully examine receipt")
    assert "You choose your words with care." not in response.get("narration", "")
    assert response["outcome"]["accepted"] is True
    assert len(response["view"]["discovered"]) == 1


def test_ambiguous_or_absent_approach_defaults_to_neutral() -> None:
    assert approach_cue("I ask Quill") == ""
    assert approach_cue("I gently but sternly ask Quill") == ""
    assert approach_cue("I want to inject SEALED_SOLUTION") == ""


def test_model_does_not_receive_raw_player_demeanor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ai = LocalAI(model="mock")
    seen: list[dict[str, Any]] = []

    def fake(_self: LocalAI, _system: str, payload: dict[str, Any]) -> dict[str, str]:
        seen.append(payload)
        return {"tone": "neutral"}

    monkeypatch.setattr(LocalAI, "_ask", fake)
    game = DemoGame(ai=ai)
    result = game.act("I softly ask Quill what he heard")
    assert "You keep your voice gentle." in result["narration"]
    assert all("softly" not in str(item) for item in seen)

