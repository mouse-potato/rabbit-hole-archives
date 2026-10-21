"""Read-only inquiries do not mutate evidence or leak undiscovered facts."""
from __future__ import annotations

from typing import Any

import pytest

from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI


@pytest.mark.parametrize("question", [
    "what's in the study?",
    "what is in the room?",
    "look around",
    "describe the scene",
    "where am i?",
])
def test_scene_question_is_read_only_and_mentions_visible_objects(question: str) -> None:
    game = DemoGame()
    before = game.packet()
    response = game.act(question)
    assert response["outcome"]["action"] == "inquire"
    assert response["outcome"]["accepted"] is True
    assert "study" in response["outcome"]["detail"].lower()
    assert "Receipt" in response["outcome"]["detail"]
    assert "Porter Quill" in response["outcome"]["detail"]
    assert response["view"] == before["view"]
    assert response["view"]["discovered"] == []


def test_inquiry_after_moving_uses_current_public_context() -> None:
    game = DemoGame()
    game.act("go to hall")
    response = game.act("what's in the hall?")
    assert response["outcome"]["action"] == "inquire"
    assert "Glove" in response["outcome"]["detail"]
    assert "Maid Rosalind" in response["outcome"]["detail"]
    assert response["view"]["place_key"] == "hall"
    assert response["view"]["discovered"] == []


def test_other_room_question_does_not_teleport() -> None:
    game = DemoGame()
    response = game.act("what's in the hall?")
    assert response["outcome"]["action"] == "inquire"
    assert "visit the hall" in response["outcome"]["detail"]
    assert response["view"]["place_key"] == "study"


def test_casebook_review_reveals_only_recorded_information() -> None:
    game = DemoGame()
    empty = game.act("what do i know?")
    assert "no recorded evidence" in empty["outcome"]["detail"]
    game.act("examine receipt")
    response = game.act("review my evidence")
    assert "Ada Vance" in response["outcome"]["detail"]
    assert "damp riding glove" not in response["outcome"]["detail"]
    assert "culprit_match" not in str(response)


def test_unknown_questions_do_not_invent_witness_appearance() -> None:
    game = DemoGame()
    before = game.packet()
    response = game.act("what does porter quill look like?")
    assert response["outcome"]["action"] == "inquire"
    assert "does not establish" in response["outcome"]["detail"]
    assert response["view"] == before["view"]


def test_model_cannot_reinterpret_scene_question_as_move(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ai = LocalAI(model="mock")
    requests: list[dict[str, Any]] = []

    def model(_self: LocalAI, _system: str, payload: dict[str, Any]) -> dict[str, str]:
        requests.append(payload)
        return {"action": "go to", "target": "hall"}

    monkeypatch.setattr(LocalAI, "_ask", model)
    game = DemoGame(ai=ai)
    response = game.act("what's in the hall?")
    assert response["outcome"]["action"] == "inquire"
    assert response["view"]["place_key"] == "study"
    assert requests == []


def test_existing_accusations_still_require_evidence() -> None:
    game = DemoGame()
    game.act("what's in the hall?")
    premature = game.act("accuse ada")
    assert premature["outcome"]["verdict"] == "unproven"
    game.act("examine receipt")
    game.act("go to hall")
    game.act("examine glove")
    solved = game.act("accuse ada")
    assert solved["view"]["solved"] is True
