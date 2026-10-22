"""Local demo playthrough, invalid actions, and sealed-fact checks."""
from __future__ import annotations

import pytest
from bunnyland_archives.demo_server import DemoGame


def test_demo_requires_both_rooms_and_clues_to_solve() -> None:
    game = DemoGame()
    initial = game.packet()
    assert initial["view"]["solved"] is False
    assert initial["view"]["discovered"] == []
    assert "explanation" not in str(initial)
    assert "culprit_match" not in str(initial)
    assert [item["key"] for item in initial["options"]["evidence"]] == ["receipt"]

    questioned = game.act("talk to porter")
    assert questioned["outcome"]["accepted"] is True
    assert len(questioned["view"]["heard"]) == 1

    first = game.act("examine receipt")
    assert "Ada Vance" in first["outcome"]["observation"]
    repeated = game.act("examine receipt")
    assert len(repeated["view"]["discovered"]) == 1

    # A correct guess is not enough: the physical link from the hall is missing.
    premature = game.act("accuse ada")
    assert premature["outcome"]["verdict"] == "unproven"
    assert premature["view"]["solved"] is False

    wrong = game.act("accuse halloran")
    assert wrong["outcome"]["verdict"] == "unproven"
    assert wrong["view"]["solved"] is False

    moved = game.act("go to hall")
    assert moved["view"]["place_key"] == "hall"
    assert [item["key"] for item in moved["options"]["evidence"]] == ["glove"]
    heard = game.act("talk to maid")
    assert heard["outcome"]["accepted"] is True
    examined = game.act("examine glove")
    assert examined["outcome"]["accepted"] is True
    assert len(examined["view"]["discovered"]) == 2

    solved = game.act("accuse ada")
    assert solved["outcome"]["verdict"] == "solved"
    assert solved["view"]["solved"] is True
    assert "culprit_match" not in str(solved)
    assert "missing_evidence" not in str(solved)


def test_demo_invalid_actions_and_room_change() -> None:
    game = DemoGame()
    unknown = game.act("examine treasure")
    assert unknown["outcome"]["accepted"] is False
    assert unknown["view"]["discovered"] == []

    far = game.act("talk to maid")
    assert far["outcome"]["accepted"] is False
    assert "not here" in far["outcome"]["detail"]

    too_long = game.act("x" * 301)
    assert too_long["outcome"]["accepted"] is False

    invalid_room = game.act("go to attic")
    assert invalid_room["outcome"]["accepted"] is False
    assert invalid_room["view"]["place_key"] == "study"

    moved = game.act("go to hall")
    assert moved["view"]["place_key"] == "hall"
    assert [item["key"] for item in moved["options"]["evidence"]] == ["glove"]


def test_demo_never_serializes_sealed_case() -> None:
    game = DemoGame()
    for packet in [
        game.packet(),
        game.act("accuse ada"),
        game.act("examine receipt"),
        game.act("go to hall"),
        game.act("examine glove"),
        game.act("accuse ada"),
    ]:
        text = str(packet)
        assert "Ada signed the seal out and concealed it" not in text
        assert "theft" not in text
        assert "supporting_evidence" not in text
        assert "culprit_match" not in text
        assert "missing_evidence" not in text


@pytest.mark.parametrize("command", [
    "go to hall",
    "go to the hall",
    "move to the hall",
    "travel to the hall",
    "visit the hall",
    "walk into the hall",
    "walk to hall",
    "enter hall",
    "go to The Hall!",
])
def test_demo_recognizes_natural_travel_phrases(command: str) -> None:
    game = DemoGame()
    moved = game.act(command)
    assert moved["outcome"]["accepted"] is True
    assert moved["view"]["place_key"] == "hall"


@pytest.mark.parametrize("command", [
    "interview the maid",
    "speak to the maid",
    "talk to the maid",
    "question maid",
])
def test_demo_recognizes_interview_phrases(command: str) -> None:
    game = DemoGame()
    game.act("go to the hall")
    questioned = game.act(command)
    assert questioned["outcome"]["accepted"] is True
    assert len(questioned["view"]["heard"]) == 1


def test_solved_case_rejects_subsequent_actions() -> None:
    game = DemoGame()
    game.act("examine receipt")
    game.act("go to hall")
    game.act("examine glove")
    won = game.act("accuse ada")
    assert won["view"]["solved"] is True

    for command in ("accuse halloran", "examine glove", "go to study"):
        rejected = game.act(command)
        assert rejected["outcome"]["accepted"] is False
        assert "closed" in rejected["outcome"]["detail"]
        assert rejected["view"]["solved"] is True
        assert rejected["view"]["place_key"] == "hall"

