"""Deterministic, LLM-free harness for the archive plugin.

The pattern mirrors Bunnyland's own handler-level tests: build a real ``WorldActor``,
apply the plugin through the real plugin loader, then execute one command against the
handler and apply its mutation plan. No model calls, controllers, or autonomous ticks.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, cast

from bunnyland.core import (
    ActionPointsComponent,
    CharacterComponent,
    CommandCost,
    ContainmentMode,
    Contains,
    FocusPointsComponent,
    HandlerContext,
    HandlerResult,
    IdentityComponent,
    InitiativeComponent,
    Lane,
    LLMControllerComponent,
    WorldActor,
    build_submitted_command,
    container_of,
    spawn_entity,
)
from bunnyland.plugins import apply_plugins
from bunnyland_archives import (
    COMMAND_TYPE,
    PLUGIN_ID,
    ArchiveNarratorView,
    ExamineEvidenceHandler,
    ImportedCase,
    apply_handler_result,
    archive_plugin,
    import_case,
)
from bunnyland_archives.components import InvestigatorSessionComponent
from rabbit_hole_engine.authoring import CaseDefinition
from relics import Entity, EntityId, World


def case_data() -> dict[str, Any]:
    """A two-room case: one clue at the start, one out of reach from the start."""

    return {
        "schema_version": 1,
        "id": "missing_seal",
        "title": "The Missing Seal",
        "start_location": "study",
        "locations": [
            {"id": "study", "name": "The Study"},
            {"id": "hall", "name": "The Hall"},
        ],
        "events": [
            {"id": "theft", "description": "Ada signed for the seal at the desk."},
            {"id": "departure", "description": "Ada left the hall with a heavy glove."},
        ],
        "suspects": [{"id": "ada", "name": "Ada Vance"}],
        "evidence": [
            {
                "id": "receipt",
                "location": "study",
                "observation": "A signed receipt for the seal, in Ada's hand.",
                "source_event": "theft",
            },
            {
                "id": "glove",
                "location": "hall",
                "observation": "A single glove, still damp.",
                "source_event": "departure",
            },
        ],
        "solution": {
            "culprit": "ada",
            "explanation": "Ada signed for the seal and carried it out.",
            "supporting_evidence": ["receipt"],
        },
    }


def build_case(data: dict[str, Any] | None = None) -> CaseDefinition:
    return CaseDefinition.model_validate_json(json.dumps(data or case_data()))


@dataclass
class ArchiveScenario:
    actor: WorldActor
    imported: ImportedCase
    case: CaseDefinition
    character: EntityId
    controller: EntityId
    generation: int

    @property
    def world(self) -> World:
        return self.actor.world

    def ctx(self) -> HandlerContext:
        return HandlerContext(world=self.world, epoch=self.actor.epoch)

    def room_of(self, entity_id: EntityId) -> EntityId | None:
        return cast(EntityId | None, container_of(self.world.get_entity(entity_id)))


def build_scenario(case: CaseDefinition | None = None) -> ArchiveScenario:
    """Apply the plugin to a fresh actor and import one case."""

    actor = WorldActor()
    apply_plugins([archive_plugin()], actor)
    resolved = case or build_case()
    imported = import_case(actor.world, resolved)

    character = spawn_entity(
        actor.world,
        [
            IdentityComponent(name="Vera Holt", kind="character"),
            CharacterComponent(species="bunny"),
            ActionPointsComponent(current=5.0, maximum=5.0, regen_per_hour=1.0),
            FocusPointsComponent(current=3.0, maximum=3.0, regen_per_hour=0.5),
            InitiativeComponent(score=1.0),
            InvestigatorSessionComponent(case_key=resolved.id),
        ],
    )
    actor.world.get_entity(imported.places[resolved.start_location]).add_relationship(
        Contains(mode=ContainmentMode.ROOM_CONTENT), character.id
    )
    controller = spawn_entity(
        actor.world,
        [LLMControllerComponent(profile_name="default", model="deterministic-test")],
    )
    generation = actor.assign_controller(character.id, controller.id)

    return ArchiveScenario(
        actor=actor,
        imported=imported,
        case=resolved,
        character=character.id,
        controller=controller.id,
        generation=generation,
    )


def examine_command(scenario: ArchiveScenario, target_id: EntityId | str) -> Any:
    return build_submitted_command(
        character_id=str(scenario.character),
        controller_id=str(scenario.controller),
        controller_generation=scenario.generation,
        command_type=COMMAND_TYPE,
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={"target_id": str(target_id)},
    )


def examine(scenario: ArchiveScenario, target_id: EntityId | str) -> HandlerResult:
    """Execute the examination handler and apply its mutation plan."""

    handler = ExamineEvidenceHandler()
    ctx = scenario.ctx()
    result = handler.execute(ctx, examine_command(scenario, target_id))
    apply_handler_result(ctx, result)
    return result


def move_to(scenario: ArchiveScenario, place_key: str) -> None:
    """Place the investigator in another canonical room (bypassing travel mechanics)."""

    character = scenario.world.get_entity(scenario.character)
    room_id = scenario.room_of(scenario.character)
    if room_id is not None:
        scenario.world.get_entity(room_id).remove_relationship(Contains, scenario.character)
    scenario.world.get_entity(scenario.imported.places[place_key]).add_relationship(
        Contains(mode=ContainmentMode.ROOM_CONTENT), character.id
    )


def discovery_entities(scenario: ArchiveScenario) -> list[Entity]:
    from bunnyland_archives.components import DiscoveryComponent

    return list(
        scenario.world.query().with_all([DiscoveryComponent]).execute_entities()
    )


def canonical_snapshot(
    scenario: ArchiveScenario,
    components: Iterable[type] | None = None,
) -> dict[tuple[str, str], str]:
    """Serialize every canonical component so tests can prove exact immutability."""

    from bunnyland_archives.components import CANONICAL_COMPONENTS

    wanted = tuple(components or CANONICAL_COMPONENTS)
    snapshot: dict[tuple[str, str], str] = {}
    for entity in scenario.world.query().execute_entities():
        for component_type in wanted:
            if entity.has_component(component_type):
                component: Any = entity.get_component(component_type)
                snapshot[(str(entity.id), component_type.__name__)] = repr(component)
    return snapshot


def narrator_projection(scenario: ArchiveScenario) -> ArchiveNarratorView:
    from bunnyland_archives import narrator_view

    return narrator_view(scenario.world, scenario.character)


def save_and_reload(scenario: ArchiveScenario) -> ArchiveScenario:
    """Round-trip the world through Bunnyland's own save/load path.

    Entity identifiers are stable across the round-trip, so the reloaded scenario
    keeps the same case and investigator references.
    """

    import tempfile
    from pathlib import Path

    from bunnyland.persistence import WorldMeta, load_world, save_world
    from bunnyland.plugins import PluginRegistry

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "world.json"
        save_world(
            scenario.actor,
            path,
            meta=WorldMeta(plugins=(PLUGIN_ID,), seed="round-trip"),
        )
        actor, _meta = load_world(path, registry=PluginRegistry([archive_plugin()]))

    return ArchiveScenario(
        actor=actor,
        imported=scenario.imported,
        case=scenario.case,
        character=scenario.character,
        controller=scenario.controller,
        generation=scenario.generation,
    )
