"""Witness follow-ups only quote testimony already recorded for this investigator."""
from __future__ import annotations

from typing import Any

import pytest
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI


def test_not_yet_interviewed_witness_has_no_testimony() -> None:
    game = DemoGame()
    before = game.packet()
    result = game.act("what does Quill know about the seal?")
    assert result["outcome"]["action"] == "inquire"
    assert "not recorded any testimony" in result["outcome"]["detail"]
    assert result["view"] == before["view"]


def test_topic_followup_quotes_only_matching_porter_statement() -> None:
    game = DemoGame()
    game.act("talk to porter")
    game.act("ask Quill about receipt")
    receipt = game.act("what did Quill say about the receipt?")
    assert receipt["outcome"]["action"] == "inquire"
    assert "Both names are on the desk receipt" in receipt["outcome"]["detail"]
    assert "arguing" not in receipt["outcome"]["detail"]
    seal = game.act("what did Porter hear about the seal?")
    assert "arguing" in seal["outcome"]["detail"]
    assert "desk receipt" not in seal["outcome"]["detail"]


def test_witness_followup_unknown_topic_does_not_invent() -> None:
    game = DemoGame()
    game.act("talk to porter")
    game.act("ask Quill about receipt")
    result = game.act("what does Quill know about the train?")
    assert "does not address that topic" in result["outcome"]["detail"]
    assert "train" not in str(result["view"])


def test_other_witness_cannot_reveal_unheard_testimony() -> None:
    game = DemoGame()
    game.act("talk to porter")
    game.act("ask Quill about receipt")
    game.act("go to hall")
    result = game.act("what did Rosalind say about the glove?")
    assert "not recorded any testimony" in result["outcome"]["detail"]
    assert "glove" not in str(result["view"]["heard"])
    game.act("talk to maid")
    after = game.act("what did Rosalind say about the glove?")
    assert "riding gloves" in after["outcome"]["detail"]


def test_followup_does_not_call_model_or_mutate_casebook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ai = LocalAI(model="mock")
    requested: list[dict[str, Any]] = []

    def responder(_self: LocalAI, _system: str, payload: dict[str, Any]) -> dict[str, str]:
        requested.append(payload)
        return {"tone": "neutral"}

    monkeypatch.setattr(LocalAI, "_ask", responder)
    game = DemoGame(ai=ai)
    game.act("talk to porter")
    game.act("ask Quill about receipt")
    requested.clear()
    before = game.packet()
    result = game.act("what did Porter say about the receipt?")
    assert "desk receipt" in result["outcome"]["detail"]
    assert result["view"] == before["view"]
    assert requested == []


@pytest.mark.parametrize("player_text", [
    "what does Porter Quill look like?",
    "tell me about Ada",
    "I accuse Ada Vance",
    "can I go to hall?",
])
def test_other_inquiry_and_action_routes_unchanged(player_text: str) -> None:
    game = DemoGame()
    result = game.act(player_text)
    assert result["outcome"]["action"] != "inquire" or (
        "Your casebook records the witness saying" not in result["outcome"]["detail"]
    )

