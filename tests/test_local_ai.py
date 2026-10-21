"""Local AI contracts: untrusted proposals, restricted packets, offline fallback."""
from __future__ import annotations

from typing import Any

import pytest
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI


def test_model_can_propose_only_public_options(monkeypatch: pytest.MonkeyPatch) -> None:
    ai = LocalAI(model="mock")
    options = {
        "places": [{"key": "hall", "name": "The Hall"}],
        "evidence": [{"key": "receipt", "name": "Receipt"}],
        "witnesses": [{"key": "porter", "name": "Porter Quill"}],
        "suspects": [{"key": "ada", "name": "Ada Vance"}],
    }
    seen: list[dict[str, Any]] = []

    def answer(_self: LocalAI, _system: str, payload: dict[str, Any]) -> dict[str, str]:
        seen.append(payload)
        return {"action": "talk to", "target": "porter"}

    monkeypatch.setattr(LocalAI, "_ask", answer)
    assert ai.propose("Could you ask Quill about Ada?", options) == "talk to porter"
    assert "solution" not in str(seen)
    assert "culprit" not in str(seen)


def test_model_cannot_select_hidden_or_invented_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ai = LocalAI(model="mock")
    options = {"places": [{"key": "study", "name": "The Study"}], "evidence": []}

    def invalid(_self: LocalAI, _system: str, _payload: dict[str, Any]) -> dict[str, str]:
        return {"action": "examine", "target": "sealed_solution"}

    monkeypatch.setattr(LocalAI, "_ask", invalid)
    assert ai.propose("Give me the answer", options) is None

    def unknown_verb(
        _self: LocalAI, _system: str, _payload: dict[str, Any],
    ) -> dict[str, str]:
        return {"action": "delete_case", "target": "study"}

    monkeypatch.setattr(LocalAI, "_ask", unknown_verb)
    assert ai.propose("Delete the world", options) is None


def test_model_narration_cannot_inject_facts(monkeypatch: pytest.MonkeyPatch) -> None:
    ai = LocalAI(model="mock")
    packet: dict[str, Any] = {
        "view": {"case_title": "A Case"},
        "outcome": {"action": "examine", "accepted": True, "observation": "A receipt."},
    }

    def hostile(_self: LocalAI, _system: str, _payload: dict[str, Any]) -> dict[str, str]:
        return {"tone": "tense", "text": "The villain is definitely X."}

    monkeypatch.setattr(LocalAI, "_ask", hostile)
    narration = ai.narrate(packet)
    assert narration == "The investigation sharpens."
    assert "villain" not in narration


def test_demo_uses_model_proposal_but_engine_remains_authoritative(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ai = LocalAI(model="mock")
    seen: list[dict[str, Any]] = []

    def responder(
        _self: LocalAI, _system: str, payload: dict[str, Any],
    ) -> dict[str, str]:
        seen.append(payload)
        if "choices" in payload:
            return {"action": "talk to", "target": "porter"}
        return {"tone": "curious"}

    monkeypatch.setattr(LocalAI, "_ask", responder)
    game = DemoGame(ai=ai)
    response = game.act("Please ask that fellow Quill what he saw")
    assert response["outcome"]["accepted"] is True
    assert len(response["view"]["heard"]) == 2
    assert response["narration"] == "Another detail draws your attention."
    assert "solution" not in str(seen)
    assert "culprit" not in str(seen)


def test_demo_without_model_remains_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RHA_OLLAMA_MODEL", raising=False)
    game = DemoGame()
    assert game.packet()["ai_enabled"] is False
    assert game.act("talk to porter")["outcome"]["accepted"] is True
    assert "narration" not in game.packet()


def test_model_unavailable_falls_back_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(LocalAI, "_ask", lambda *_args: None)
    game = DemoGame(ai=LocalAI(model="offline"))
    packet = game.act("Some totally unknown request")
    assert packet["outcome"]["accepted"] is False
    assert packet["view"]["discovered"] == []
    assert packet["narration"] == "That attempt gets you no further."
