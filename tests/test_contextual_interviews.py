"""Topic-specific interviews reuse canonical testimony and preserve the case."""
from __future__ import annotations

from typing import Any

import pytest
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI


def test_receipt_question_returns_only_relevant_porter_statement() -> None:
    game = DemoGame()
    result = game.act("I ask Quill about the receipt")
    assert result["outcome"]["accepted"] is True
    assert len(result["outcome"]["statements"]) == 1
    assert "desk receipt" in result["outcome"]["statements"][0]
    assert "arguing" not in str(result["outcome"]["statements"])
    assert len(result["view"]["heard"]) == 1
    assert result["view"]["discovered"] == []


def test_unspecific_interview_reveals_only_the_opening_statement() -> None:
    result = DemoGame().act("talk to porter")
    assert len(result["outcome"]["statements"]) == 1
    assert "arguing" in result["outcome"]["statements"][0]
    assert result["conversation"]["lead_topics"] == []


def test_unknown_topic_cannot_fabricate_answer() -> None:
    result = DemoGame().act("ask Quill about the spaceship")
    assert result["outcome"]["accepted"] is True
    assert result["outcome"]["statements"] == []
    assert "does not address that topic" in result["outcome"]["detail"]
    assert "spaceship" not in str(result["view"])


def test_topic_specific_interview_records_only_selected_testimony() -> None:
    targeted = DemoGame().act("ask Quill about receipt")
    complete = DemoGame().act("talk to porter")
    assert targeted["view"]["heard"] != complete["view"]["heard"]
    assert len(targeted["view"]["heard"]) == 1
    assert "arguing" not in str(targeted["view"]["heard"])
    assert targeted["view"]["solved"] is False


@pytest.mark.parametrize("player_text", [
    "ask Quill about the receipt",
    "talk to Porter about receipt",
    "question Quill regarding the receipt",
])
def test_topic_phrases_route_to_interview(player_text: str) -> None:
    result = DemoGame().act(player_text)
    assert result["outcome"]["accepted"] is True
    assert len(result["outcome"]["statements"]) == 1



@pytest.mark.parametrize("use_ai", [False, True])
def test_witness_named_in_topic_does_not_replace_addressee(
    use_ai: bool, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def model(_self: LocalAI, _system: str, payload: dict[str, Any]) -> dict[str, str]:
        assert "choices" not in payload, "a named addressee should resolve deterministically"
        return {"tone": "neutral"}

    monkeypatch.setattr(LocalAI, "_ask", model)
    game = DemoGame(ai=LocalAI(model="mock") if use_ai else None)
    game.act("go to the hall")
    before = game.packet()["view"]
    result = game.act("I want to ask Quill about Rosalind.")
    assert not result["outcome"]["accepted"]
    assert "That witness is not here." in result["outcome"]["detail"]
    assert result["view"] == before
    assert result["conversation"] is None

    game.act("go back to the study")
    result = game.act("I ask Quill about Rosalind.")
    assert result["outcome"]["witness_key"] == "porter"
    assert result["outcome"]["statements"] == []
    assert result["view"]["heard"] == []
