"""Opt-in inference logging never exposes player text or private case data."""
from __future__ import annotations

from typing import Any

import pytest
from bunnyland_archives.local_ai import LocalAI


def test_diagnostics_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("RHA_AI_DEBUG", raising=False)
    ai = LocalAI(model="fake")
    monkeypatch.setattr(LocalAI, "_ask", lambda *_args: {"action": "delete", "target": "receipt"})
    assert ai.propose("PRIVATE PLAYER TEXT", {"evidence": [{"key": "receipt"}]}) is None
    assert capsys.readouterr().err == ""


def test_diagnostics_report_invalid_action_without_payload(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("RHA_AI_DEBUG", "1")
    ai = LocalAI(model="fake")
    monkeypatch.setattr(LocalAI, "_ask", lambda *_args: {"action": "examine", "target": "SEALED_SECRET"})
    assert ai.propose("PRIVATE PLAYER TEXT", {"evidence": [{"key": "receipt"}]}) is None
    log = capsys.readouterr().err
    assert "intent: target_not_available" in log
    assert "SEALED_SECRET" not in log
    assert "PRIVATE PLAYER TEXT" not in log


def test_diagnostics_distinguish_transport_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("RHA_AI_DEBUG", "yes")
    ai = LocalAI(model="fake")

    def offline(*_args: Any, **_kwargs: Any) -> Any:
        raise TimeoutError("secret network details")

    monkeypatch.setattr("bunnyland_archives.local_ai.urlopen", offline)
    assert ai._ask("system", {"choices": [], "player_text": "secret"}) is None
    log = capsys.readouterr().err
    assert "intent: connection_or_timeout_failure" in log
    assert "secret" not in log


def test_narration_diagnostics_do_not_echo_model_text(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("RHA_AI_DEBUG", "true")
    ai = LocalAI(model="fake")
    monkeypatch.setattr(LocalAI, "_ask", lambda *_args: {"tone": "invented", "text": "SEALED_SECRET"})
    packet: dict[str, Any] = {
        "view": {"case_title": "Case"},
        "outcome": {"action": "move", "accepted": True},
    }
    assert ai.narrate(packet) == "You take in your new surroundings."
    log = capsys.readouterr().err
    assert "narration: invalid_tone_using_neutral" in log
    assert "SEALED_SECRET" not in log
