"""Topic-specific interviews reuse canonical testimony and preserve the case."""
from __future__ import annotations

import pytest
from bunnyland_archives.demo_server import DemoGame


def test_receipt_question_returns_only_relevant_porter_statement() -> None:
    game = DemoGame()
    result = game.act("I ask Quill about the receipt")
    assert result["outcome"]["accepted"] is True
    assert len(result["outcome"]["statements"]) == 1
    assert "desk receipt" in result["outcome"]["statements"][0]
    assert "arguing" not in str(result["outcome"]["statements"])
    assert len(result["view"]["heard"]) == 2
    assert result["view"]["discovered"] == []


def test_unspecific_interview_keeps_full_canonical_account() -> None:
    result = DemoGame().act("talk to porter")
    assert len(result["outcome"]["statements"]) == 2


def test_unknown_topic_cannot_fabricate_answer() -> None:
    result = DemoGame().act("ask Quill about the spaceship")
    assert result["outcome"]["accepted"] is True
    assert result["outcome"]["statements"] == []
    assert "does not address that topic" in result["outcome"]["detail"]
    assert "spaceship" not in str(result["view"])


def test_topic_specific_interview_keeps_authoritative_casebook() -> None:
    targeted = DemoGame().act("ask Quill about receipt")
    complete = DemoGame().act("talk to porter")
    assert targeted["view"]["heard"] == complete["view"]["heard"]
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
