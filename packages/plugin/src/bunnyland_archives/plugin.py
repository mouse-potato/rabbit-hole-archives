"""Canonical ``bunnyland.archives`` plugin entrypoint.

Bunnyland discovers out-of-tree plugins through the ``bunnyland.plugins`` entry-point
group (see ``pyproject.toml``); the loader calls :func:`bunnyland_plugins`. The plugin is
opt-in, so a world is loaded with ``bunnyland serve --plugin bunnyland.archives``.
"""

from __future__ import annotations

from bunnyland.plugins import (
    CommandContribution,
    ContentContribution,
    EcsContribution,
    Plugin,
    PluginPlacement,
)

from .actions import ACTION_DEFINITIONS
from .components import COMPONENT_TYPES, EDGE_TYPES
from .mechanics import (
    AccusationResolvedEvent,
    AccuseSuspectHandler,
    EvidenceExaminedEvent,
    ExamineEvidenceHandler,
    TalkToWitnessHandler,
    WitnessQuestionedEvent,
)

PLUGIN_ID = "bunnyland.archives"
PLUGIN_VERSION = "0.1.0"


def archive_plugin() -> Plugin:
    """Return the Rabbit Hole Archives detective mechanics plugin."""

    return Plugin(
        id=PLUGIN_ID,
        name="Rabbit Hole Archives",
        version=PLUGIN_VERSION,
        placement=PluginPlacement.ADDON,
        # Opt-in: a detective case world should not gain archive actions by default.
        default_enabled=False,
        ecs=EcsContribution(
            components=COMPONENT_TYPES,
            edges=EDGE_TYPES,
        ),
        commands=CommandContribution(
            action_definitions=ACTION_DEFINITIONS,
            action_handlers=(
                ExamineEvidenceHandler,
                TalkToWitnessHandler,
                AccuseSuspectHandler,
            ),
            typed_events=(
                EvidenceExaminedEvent,
                WitnessQuestionedEvent,
                AccusationResolvedEvent,
            ),
        ),
        content=ContentContribution(),
    )


def bunnyland_plugins() -> list[Plugin]:
    """Module-level plugin factory used by Bunnyland's plugin loader."""

    return [archive_plugin()]


__all__ = [
    "PLUGIN_ID",
    "PLUGIN_VERSION",
    "archive_plugin",
    "bunnyland_plugins",
]
