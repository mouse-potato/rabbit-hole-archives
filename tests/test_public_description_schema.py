"""Authoring-to-ECS proof for optional public descriptive text."""
from __future__ import annotations

import json
from copy import deepcopy

import pytest
from bunnyland.core import (
    ActionPointsComponent,
    CharacterComponent,
    ContainmentMode,
    Contains,
    FocusPointsComponent,
    IdentityComponent,
    InitiativeComponent,
    spawn_entity,
)
from bunnyland.core.world_actor import WorldActor
from bunnyland_archives import (
    ArchivePlaceComponent,
    ArchiveWitnessComponent,
    InvestigatorSessionComponent,
    import_case,
    narrator_view,
)
from pydantic import ValidationError
from rabbit_hole_engine.authoring import CaseDefinition

from archive_harness import case_data


def make_case() -> CaseDefinition:
    data = deepcopy(case_data())
    data["schema_version"] = 2
    data["locations"][0]["description"] = "A clock marks the study's silence."
    data["witnesses"] = [{
        "id": "porter", "name": "Porter Quill", "location": "study",
        "appearance": "The porter wears a dark waistcoat.",
    }]
    return CaseDefinition.model_validate_json(json.dumps(data))


def test_public_description_round_trip_and_import() -> None:
    case = make_case()
    again = CaseDefinition.model_validate_json(case.model_dump_json())
    assert again.locations[0].description == "A clock marks the study's silence."
    assert again.witnesses[0].appearance == "The porter wears a dark waistcoat."
    actor = WorldActor()
    imported = import_case(actor.world, case)
    place = actor.world.get_entity(imported.places["study"]).get_component(
        ArchivePlaceComponent,
    )
    witness = actor.world.get_entity(imported.witnesses["porter"]).get_component(
        ArchiveWitnessComponent,
    )
    assert place.description == case.locations[0].description
    assert witness.appearance == case.witnesses[0].appearance


def test_public_description_is_projected_only_from_present_room() -> None:
    case = make_case()
    actor = WorldActor()
    imported = import_case(actor.world, case)
    character = spawn_entity(
        actor.world,
        [
            IdentityComponent(name="Investigator", kind="character"),
            CharacterComponent(species="bunny"),
            ActionPointsComponent(current=5, maximum=5, regen_per_hour=1),
            FocusPointsComponent(current=3, maximum=3, regen_per_hour=1),
            InitiativeComponent(score=1),
            InvestigatorSessionComponent(case_key=case.id),
        ],
    )
    actor.world.get_entity(imported.places["study"]).add_relationship(
        Contains(mode=ContainmentMode.ROOM_CONTENT), character.id,
    )
    view = narrator_view(actor.world, character.id)
    assert view.place_description == "A clock marks the study's silence."
    assert len(view.witnesses) == 1
    assert view.witnesses[0].appearance == "The porter wears a dark waistcoat."
    assert view.discovered == ()
    assert "culprit" not in view.model_dump_json()


@pytest.mark.parametrize("bad_description", ["", "   "])
def test_empty_authored_description_rejected(bad_description: str) -> None:
    data = deepcopy(case_data())
    data["locations"][0]["description"] = bad_description
    with pytest.raises(ValidationError):
        CaseDefinition.model_validate_json(json.dumps(data))


def test_optional_description_does_not_break_legacy_cases() -> None:
    legacy = CaseDefinition.model_validate_json(json.dumps(case_data()))
    assert legacy.locations[0].description is None
    assert legacy.witnesses == ()
