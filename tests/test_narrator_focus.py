"""Model-selected narration focus references only publicly available details."""
from __future__ import annotations

from typing import Any

import pytest
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI, public_focus_options


def test_no_unexamined_evidence_appears_as_focus_option() -> None:
    game = DemoGame()
    packet = game.packet()
    packet["outcome"] = {"action": "move", "accepted": True}
    choices = public_focus_options(packet)
    assert "clue:receipt" not in choices
    assert "clue:glove" not in choices
    assert "witness:porter" in choices
    assert "witness:maid" not in choices


def test_model_can_select_recorded_evidence_not_invent_its_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[dict[str, Any]] = []

    def model(_self: LocalAI, _system: str, payload: dict[str, Any]) -> dict[str, str]:
        seen.append(payload)
        return {"tone": "curious", "focus": "clue:receipt", "text": "SEALED_SOLUTION"}

    monkeypatch.setattr(LocalAI, "_ask", model)
    game = DemoGame(ai=LocalAI(model="mock"))
    result = game.act("examine receipt")
    assert "The receipt remains in your casebook." in result["narration"]
    assert "SEALED_SOLUTION" not in result["narration"]
    assert "clue:receipt" in seen[-1]["focus_options"]
    assert "clue:glove" not in seen[-1]["focus_options"]
    assert "solution" not in str(seen)


def test_unavailable_model_focus_cannot_reveal_absent_witness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(LocalAI, "_ask", lambda *_args: {
        "tone": "neutral", "focus": "witness:maid",
        "text": "Maid Rosalind is guilty!",
    })
    game = DemoGame(ai=LocalAI(model="mock"))
    response = game.act("examine receipt")
    assert "Rosalind" not in response["narration"]
    assert "guilty!" not in response["narration"]


def test_focus_does_not_reveal_unheard_witness_statements() -> None:
    game = DemoGame()
    p = game.packet()
    p["outcome"] = {"action": "move", "accepted": True}
    assert not any(k.startswith("testimony:") for k in public_focus_options(p))
    game.act("talk to porter")
    later = game.packet()
    later["outcome"] = {"action": "move", "accepted": True}
    choices = public_focus_options(later)
    assert any(k.startswith("testimony:") for k in choices)
    assert "Ada hurried through the hall" not in str(choices)


def test_rejected_actions_never_offer_narrative_focus() -> None:
    game = DemoGame()
    p = game.packet()
    p["outcome"] = {"action": "accuse", "accepted": False}
    assert public_focus_options(p) == {}
