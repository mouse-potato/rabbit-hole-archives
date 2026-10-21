"""Action definitions owned by ``bunnyland.archives``."""

from __future__ import annotations

from bunnyland.core import ActionDefinition
from bunnyland.core.actions import ACTION_COST, define_action

EXAMINE_EVIDENCE = define_action(
    "examine-evidence",
    ("target_id",),
    tool_name="examine_evidence",
    description=(
        "Examine a piece of case evidence you can currently reach. This returns its "
        "canonical observation and records the discovery in your casebook. Re-examining "
        "a recorded clue is safe and adds nothing new."
    ),
    cost=ACTION_COST,
    patterns=("examine {target_id}", "examine evidence {target_id}", "study {target_id}"),
)

TALK_TO_WITNESS = define_action(
    "talk-to-witness",
    ("target_id",),
    tool_name="talk_to_witness",
    description=(
        "Hear out a witness who is in your current location. Statements are attributed to "
        "the witness, arrive in a fixed order, and may point you toward a lead."
    ),
    cost=ACTION_COST,
    patterns=("talk {target_id}", "question {target_id}", "ask {target_id}"),
)

ACCUSE_SUSPECT = define_action(
    "accuse-suspect",
    ("target_id",),
    tool_name="accuse_suspect",
    description=(
        "Formally accuse a suspect. The case is solved only if you name the right person "
        "and have already recorded the evidence that supports it. The magistrate's answer "
        "never distinguishes a mistaken suspect from a thin case."
    ),
    cost=ACTION_COST,
    patterns=("accuse {target_id}", "accuse suspect {target_id}"),
)

ACTION_DEFINITIONS: tuple[ActionDefinition, ...] = (
    EXAMINE_EVIDENCE,
    TALK_TO_WITNESS,
    ACCUSE_SUSPECT,
)

__all__ = [
    "ACCUSE_SUSPECT",
    "ACTION_DEFINITIONS",
    "EXAMINE_EVIDENCE",
    "TALK_TO_WITNESS",
]
