"""Ambiguous or negated requests cannot silently select an action."""
from __future__ import annotations

from typing import Any

import pytest
from bunnyland_archives.components import COMPONENT_TYPES
from bunnyland_archives.demo_server import DemoGame
from bunnyland_archives.local_ai import LocalAI


def state(game: DemoGame) -> list[tuple[str, str, str]]:
    return sorted(
        (str(entity.id), component.__name__, repr(entity.get_component(component)))
        for entity in game.actor.world.query().execute_entities()
        for component in COMPONENT_TYPES if entity.has_component(component)
    )


@pytest.mark.parametrize("text", [
    "don't examine receipt", "don’t inspect receipt", "do not study receipt",
    "I won't go to hall", "never accuse Ada", "not talk to porter",
    "if the receipt is signed accuse Ada", "maybe inspect receipt",
    "should I accuse Ada?", "go to hall and examine glove",
    "talk to porter then ask maid", "examine receipt or glove",
    "ask Quill and Rosalind about the seal", "inspect receipt; accuse Ada",
])
def test_unclear_action_never_mutates_or_calls_model(
    text: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        pytest.fail("rejected request reached model")

    monkeypatch.setattr(LocalAI, "_ask", fail)
    game = DemoGame(ai=LocalAI(model="mock"))
    before = state(game)
    result = game.act(text)
    assert not result["outcome"]["accepted"]
    assert "No action taken" in result["outcome"]["detail"]
    assert state(game) == before


def test_names_joined_in_a_witness_topic_are_allowed() -> None:
    result = DemoGame().act("ask Quill about Halloran and Ada")
    assert result["outcome"]["accepted"]
    assert "arguing" in result["outcome"]["statements"][0]


def test_model_cannot_turn_unrelated_input_into_formal_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[dict[str, Any]] = []

    def model(_self: LocalAI, _system: str, payload: dict[str, Any]) -> dict[str, str]:
        requests.append(payload)
        return {"action": "accuse", "target": "ada"}

    monkeypatch.setattr(LocalAI, "_ask", model)
    game = DemoGame(ai=LocalAI(model="mock"))
    before = state(game)
    result = game.act("I ponder the mystery")
    assert not result["outcome"]["accepted"]
    assert state(game) == before
    choices = next(payload["choices"] for payload in requests if "choices" in payload)
    assert all(choice["action"] != "accuse" for choice in choices)
    assert game.act("I accuse Ada Vance")["outcome"]["verdict"] == "unproven"
