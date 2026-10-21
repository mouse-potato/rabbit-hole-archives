"""Local demo golden path and privacy checks (no LLM or web browser required)."""
from __future__ import annotations

from bunnyland_archives.demo_server import DemoGame


def test_demo_can_solve_the_missing_seal() -> None:
    game = DemoGame()
    initial = game.packet()
    assert initial["view"]["solved"] is False
    assert initial["view"]["discovered"] == []
    assert "explanation" not in str(initial)
    assert "culprit_match" not in str(initial)
    assert [item["key"] for item in initial["options"]["evidence"]] == ["receipt"]

    questioned = game.act("talk to porter")
    assert questioned["outcome"]["accepted"] is True
    assert len(questioned["view"]["heard"]) == 2

    first = game.act("examine receipt")
    assert first["outcome"]["observation"] == "A signed receipt for the seal, in Ada's hand."
    repeated = game.act("examine receipt")
    assert len(repeated["view"]["discovered"]) == 1

    wrong = game.act("accuse halloran")
    assert wrong["outcome"]["verdict"] == "unproven"
    assert wrong["view"]["solved"] is False

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

    moved = game.act("go to hall")
    assert moved["view"]["place_key"] == "hall"
    assert [item["key"] for item in moved["options"]["evidence"]] == ["glove"]

    heard = game.act("talk to maid")
    assert heard["outcome"]["accepted"] is True
    examined = game.act("examine glove")
    assert examined["outcome"]["accepted"] is True


def test_demo_never_serializes_sealed_case() -> None:
    game = DemoGame()
    for packet in [game.packet(), game.act("accuse ada"), game.act("examine receipt")]:
        text = str(packet)
        assert "Ada signed for the seal and carried it out" not in text
        assert "theft" not in text
        assert "supporting_evidence" not in text
        assert "culprit_match" not in text
        assert "missing_evidence" not in text
