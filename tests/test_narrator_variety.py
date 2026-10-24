"""Narration variety is reviewed, deterministic, and does not change the case."""
from __future__ import annotations

from typing import Any

import pytest
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI, trusted_narration


def test_repeated_actions_receive_distinct_reviewed_scene_beats() -> None:
    game = DemoGame()
    results = [game.act("examine receipt") for _ in range(4)]
    lines = [result["narration"] for result in results]
    assert len(set(lines[:3])) == 3
    assert lines[0] == lines[3]
    assert all(result["outcome"]["accepted"] for result in results)
    assert len(results[-1]["view"]["discovered"]) == 1


def test_narration_variant_is_not_exposed_as_game_state() -> None:
    game = DemoGame()
    initial = game.packet()
    game.act("examine receipt")
    later = game.packet()
    assert "narration_turn" not in str(later)
    assert "variation" not in str(later)
    assert initial["view"]["discovered"] == []
    assert len(later["view"]["discovered"]) == 1


def test_variation_cannot_add_authoritative_clue_or_solution() -> None:
    packet: dict[str, Any] = {
        "view": {"place_key": "study", "discovered": [], "heard": []},
        "outcome": {"action": "examine-evidence", "accepted": True},
    }
    options = [trusted_narration(packet, variation=i) for i in range(6)]
    assert len(set(options)) == 3
    assert all("Ada" not in line and "receipt" not in line for line in options)


def test_model_cannot_inject_unapproved_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ai = LocalAI(model="mock")
    monkeypatch.setattr(
        LocalAI, "_ask",
        lambda *_args: {"tone": "tense", "variation": "SECRET", "text": "SECRET"},
    )
    packet: dict[str, Any] = {
        "view": {"case_title": "Case", "place_key": "hall"},
        "outcome": {"action": "move", "accepted": True},
    }
    line = ai.narrate(packet, variation=1)
    assert "SECRET" not in line
    assert "side door" in line


def test_rejected_outcomes_stay_rejected_for_every_variation() -> None:
    packet: dict[str, Any] = {
        "view": {"place_key": "study"},
        "outcome": {"action": "examine", "accepted": False},
    }
    assert {trusted_narration(packet, variation=n) for n in range(5)} == {
        "That action cannot be completed."
    }
