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

ACTION_DEFINITIONS: tuple[ActionDefinition, ...] = (EXAMINE_EVIDENCE,)

__all__ = ["ACTION_DEFINITIONS", "EXAMINE_EVIDENCE"]
