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


@pytest.mark.parametrize("player_text", [
    "tell me about Ada",
    "tell me about Porter Quill",
])
def test_unsupported_open_ended_question_never_becomes_accusation(
    player_text: str,
) -> None:
    game = DemoGame()
    response = game.act(player_text)
    assert response["outcome"]["action"] == "inquire"
    assert "does not establish" in response["outcome"]["detail"]
    assert response["view"]["solved"] is False


def test_normal_commands_are_not_intercepted_as_inquiries() -> None:
    game = DemoGame()
    examined = game.act("examine receipt")
    assert examined["outcome"]["action"] != "inquire"
    assert examined["outcome"]["accepted"] is True
    moved = game.act("go to hall")
    assert moved["outcome"]["action"] == "move"
    assert moved["view"]["place_key"] == "hall"


@pytest.mark.parametrize("player_text", [
    "Could you ask Quill what he heard?",
    "Can I go to the hall?",
    "Would you examine the receipt?",
])
def test_polite_action_requests_are_not_swallowed(player_text: str) -> None:
    from bunnyland_archives.inquiry import inquiry

    game = DemoGame()
    assert inquiry(player_text, game.packet()) is None


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


@pytest.mark.parametrize("player_text", [
    "let's look at that recipt",
    "I'd like to look at the receipt first",
    "can I look at the receipt?",
    "I want to examine the receipt",
    "receipt??????",
    "examine receipt",
])
def test_playtest_phrasings_examine_visible_receipt(player_text: str) -> None:
    game = DemoGame()
    result = game.act(player_text)
    assert result["outcome"]["accepted"] is True
    assert result["outcome"]["action"] != "inquire"
    assert "Ada Vance" in result["outcome"]["observation"]
    assert [item["evidence_key"] for item in result["view"]["discovered"]] == ["receipt"]


def test_inspection_fallback_rejects_unavailable_or_ambiguous_targets() -> None:
    from bunnyland_archives.inquiry import evidence_command

    game = DemoGame()
    assert evidence_command("look at the glove", game.packet()["options"]) is None
    assert evidence_command("look at an unknown object", game.packet()["options"]) is None
    assert evidence_command("the receipt might be important", game.packet()["options"]) is None
    assert evidence_command(
        "look at recipt",
        {"evidence": [
            {"key": "receipt", "name": "Receipt"},
            {"key": "recipt", "name": "Recipt"},
        ]},
    ) is None
    result = game.act("I want to inspect the glove")
    assert result["view"]["discovered"] == []
    assert result["outcome"]["accepted"] is False


def test_visible_evidence_phrasing_survives_model_outage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(LocalAI, "_ask", lambda *_args: None)
    game = DemoGame(ai=LocalAI(model="offline"))
    result = game.act("I'd like to look at the receipt first")
    assert result["outcome"]["accepted"] is True
    assert len(result["view"]["discovered"]) == 1


@pytest.mark.parametrize(("player_text", "action"), [
    ("let's talk to the porter", "talk"),
    ("Ask Quill what he heard.", "talk"),
    ("I accuse Ada Vance.", "accuse"),
    ("I would like to accuse Ada Vance.", "accuse"),
    ("I want to accuse Ada.", "accuse"),
    ("Can I go to the hall?", "move"),
])
def test_transcript_action_phrasing_without_model(
    player_text: str, action: str,
) -> None:
    game = DemoGame()
    result = game.act(player_text)
    assert result["outcome"]["accepted"] is True
    assert result["outcome"]["action"] != "inquire"
    if action == "talk":
        assert result["view"]["heard"]
    elif action == "move":
        assert result["view"]["place_key"] == "hall"
    else:
        assert result["outcome"]["verdict"] == "unproven"


def test_model_outage_does_not_block_clear_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(LocalAI, "_ask", lambda *_args: None)
    game = DemoGame(ai=LocalAI(model="offline"))
    result = game.act("I accuse Ada Vance.")
    assert result["outcome"]["accepted"] is True
    assert result["outcome"]["verdict"] == "unproven"


def test_testimony_question_does_not_echo_unrelated_observation() -> None:
    game = DemoGame()
    game.act("examine receipt")
    result = game.act("does Quill know anything about the receipt?")
    assert result["outcome"]["action"] == "inquire"
    assert "ask an available witness" in result["outcome"]["detail"]
    assert "signed the seal out" not in result["outcome"]["detail"]
    assert not result["view"]["heard"]


def test_where_am_i_with_typo_still_reports_location() -> None:
    game = DemoGame()
    result = game.act("where am I right nw")
    assert result["outcome"]["action"] == "inquire"
    assert "study" in result["outcome"]["detail"].lower()


def test_unlisted_witness_cannot_be_silently_substituted_as_suspect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ai = LocalAI(model="mock")
    calls: list[dict[str, Any]] = []

    def bad_guess(
        _self: LocalAI, _system: str, payload: dict[str, Any],
    ) -> dict[str, str]:
        calls.append(payload)
        return {"action": "accuse", "target": "ada"}

    monkeypatch.setattr(LocalAI, "_ask", bad_guess)
    game = DemoGame(ai=ai)
    for player_text in ("I want to accuse the Porter.", "I accuse the Porter."):
        result = game.act(player_text)
        assert result["outcome"]["accepted"] is False
        assert "listed suspects" in result["outcome"]["detail"]
        assert result["view"]["solved"] is False
    assert all("choices" not in payload for payload in calls)


def test_negated_accusation_not_interpreted_as_action() -> None:
    from bunnyland_archives.inquiry import conversational_command

    game = DemoGame()
    assert conversational_command(
        "I don't want to accuse Ada", game._ai_options(),
    ) is None
