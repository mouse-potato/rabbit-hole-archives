"""Public authored world details are scoped to the player's current room."""
from __future__ import annotations

from bunnyland_archives.demo_server import DemoGame


def test_room_descriptions_are_authored_and_room_scoped() -> None:
    game = DemoGame()
    study = game.packet()
    assert "display cushion" in study["scene_description"]
    assert "side door" not in study["scene_description"]
    assert "porter" in study["witness_descriptions"]
    assert "maid" not in study["witness_descriptions"]
    game.act("go to hall")
    hall = game.packet()
    assert "side door" in hall["scene_description"]
    assert "maid" in hall["witness_descriptions"]
    assert "porter" not in hall["witness_descriptions"]


def test_witness_appearance_question_is_read_only() -> None:
    game = DemoGame()
    before = game.packet()
    result = game.act("what does Porter Quill look like?")
    assert result["outcome"]["action"] == "inquire"
    assert "dark waistcoat" in result["outcome"]["detail"]
    assert result["view"] == before["view"]
    assert result["view"]["discovered"] == []


def test_distant_witness_appearance_is_not_available() -> None:
    game = DemoGame()
    result = game.act("what does Rosalind look like?")
    assert "work clothes" not in result["outcome"]["detail"]
    assert "work clothes" not in str(result)
    game.act("go to hall")
    result = game.act("what does Rosalind look like?")
    assert "work clothes" in result["outcome"]["detail"]


def test_scene_question_uses_authoritative_public_description() -> None:
    game = DemoGame()
    result = game.act("look around")
    assert "display cushion" in result["outcome"]["detail"]
    assert "Receipt" in result["outcome"]["detail"]
    assert "Porter Quill" in result["outcome"]["detail"]
    assert result["view"]["discovered"] == []


def test_authored_public_descriptions_exclude_sealed_case_events() -> None:
    game = DemoGame()
    public = game.packet()
    assert "source_event" not in str(public)
    assert "supporting_evidence" not in str(public)
    assert "Ada carried the seal away concealed" not in str(public)
