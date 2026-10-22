"""Single-player localhost demo host backed by the real Bunnyland ECS.

Run: uv run python -m bunnyland_archives.demo_server
This is a development server, not a production multiuser service.
"""
from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlsplit

from bunnyland.core import (
    ActionPointsComponent,
    CharacterComponent,
    ContainmentMode,
    Contains,
    FocusPointsComponent,
    HandlerContext,
    IdentityComponent,
    InitiativeComponent,
    LLMControllerComponent,
    WorldActor,
    container_of,
    spawn_entity,
)
from bunnyland.plugins import apply_plugins
from rabbit_hole_engine.authoring import CaseDefinition

from . import (
    ArchiveEvidenceComponent,
    ArchivePlaceComponent,
    ArchiveSuspectComponent,
    InvestigatorSessionComponent,
    NarrationOutcome,
    NarrationPacket,
    apply_handler_result,
    archive_plugin,
    build_packet,
    import_case,
    perform,
    resolve_intent,
)
from .inquiry import SCENES, conversational_command, evidence_command, inquiry
from .local_ai import LocalAI, ollama_chat_endpoint, trusted_narration

WEB_ROOT = Path(__file__).resolve().parents[4] / "web"
CASE_PATH = Path(__file__).with_name("demo_case.json")


class DemoGame:
    """Own the authoritative ECS world; never serialize it to a browser."""

    def __init__(self, ai: LocalAI | None = None) -> None:
        model = os.environ.get("RHA_OLLAMA_MODEL", "").strip()
        endpoint = ollama_chat_endpoint(os.environ.get("RHA_OLLAMA_URL", "http://127.0.0.1:11434"))
        self.ai = ai if ai is not None else (
            LocalAI(model=model, endpoint=endpoint) if model else None
        )
        actor = WorldActor()
        apply_plugins([archive_plugin()], actor)
        case = CaseDefinition.model_validate_json(CASE_PATH.read_text(encoding="utf-8"))
        imported = import_case(actor.world, case)
        character = spawn_entity(
            actor.world,
            [
                IdentityComponent(name="Vera Holt", kind="character"),
                CharacterComponent(species="bunny"),
                ActionPointsComponent(current=5.0, maximum=5.0, regen_per_hour=1.0),
                FocusPointsComponent(current=3.0, maximum=3.0, regen_per_hour=0.5),
                InitiativeComponent(score=1.0),
                InvestigatorSessionComponent(case_key=case.id),
            ],
        )
        actor.world.get_entity(imported.places[case.start_location]).add_relationship(
            Contains(mode=ContainmentMode.ROOM_CONTENT), character.id
        )
        controller = spawn_entity(
            actor.world,
            [LLMControllerComponent(profile_name="default", model="demo-no-llm")],
        )
        self.generation = actor.assign_controller(character.id, controller.id)
        self.actor = actor
        self.character = character.id
        self.controller = controller.id

    def _options(self) -> dict[str, Any]:
        world = self.actor.world
        room = container_of(world.get_entity(self.character))
        place_options: list[dict[str, str]] = []
        evidence_options: list[dict[str, str]] = []
        suspects: list[dict[str, str]] = []
        for entity in world.query().with_all([ArchivePlaceComponent]).execute_entities():
            place = entity.get_component(ArchivePlaceComponent)
            place_options.append({"key": place.place_key, "name": place.name})
        for entity in world.query().with_all([ArchiveEvidenceComponent]).execute_entities():
            evidence = entity.get_component(ArchiveEvidenceComponent)
            if container_of(entity) == room:
                evidence_options.append({"key": evidence.evidence_key, "name": evidence.evidence_key.replace("-", " ").title()})
        for entity in world.query().with_all([ArchiveSuspectComponent]).execute_entities():
            suspect = entity.get_component(ArchiveSuspectComponent)
            suspects.append({"key": suspect.suspect_key, "name": suspect.name})
        return {"places": sorted(place_options, key=lambda x: x["key"]),
                "evidence": sorted(evidence_options, key=lambda x: x["key"]),
                "suspects": sorted(suspects, key=lambda x: x["key"])}

    def packet(
        self, packet: NarrationPacket | None = None, *, narrate: bool = False,
    ) -> dict[str, Any]:
        safe = (packet or build_packet(self.actor.world, self.character)).model_dump(mode="json")
        safe["options"] = self._options()
        safe["scene_description"] = SCENES.get(str(safe["view"]["place_key"]), "")
        safe["ai_enabled"] = self.ai is not None
        if narrate:
            safe["narration"] = (
                self.ai.narrate(safe) if self.ai is not None else trusted_narration(safe)
            )
        return safe

    def _ai_options(self) -> dict[str, Any]:
        options = self._options()
        view = build_packet(self.actor.world, self.character).view
        options["witnesses"] = [
            {"key": witness.witness_key, "name": witness.name}
            for witness in view.witnesses
        ]
        return options

    def act(self, text: str) -> dict[str, Any]:
        if len(text) > 300:
            return self.packet(NarrationPacket(
                view=build_packet(self.actor.world, self.character).view,
                outcome=NarrationOutcome(action="", accepted=False, detail="Command is too long."),
            ))
        # Once solved, the investigation is immutable from the player's perspective.
        # Enforce this on the server, not only through disabled browser controls.
        if build_packet(self.actor.world, self.character).view.solved:
            return self.packet(NarrationPacket(
                view=build_packet(self.actor.world, self.character).view,
                outcome=NarrationOutcome(
                    action="", accepted=False,
                    detail="This case is closed. Start a new investigation to act again.",
                ),
            ))
        # Questions and scene inspection are read-only, handled before the
        # model can mistakenly turn an inquiry into movement or examination.
        public = self.packet()
        answer = inquiry(text, public)
        if answer is not None:
            return self.packet(NarrationPacket(
                view=build_packet(self.actor.world, self.character).view,
                outcome=NarrationOutcome(action="inquire", accepted=True, detail=answer),
            ), narrate=False)
        # Reliable, narrowly scoped offline interpretation for visible evidence.
        # This also works when Ollama returns no usable proposal.
        recognized = evidence_command(text, public["options"])
        if recognized is None:
            recognized = conversational_command(text, self._ai_options())
        if recognized is not None:
            text = recognized
        elif re.search(r"\b(?:accuse|accusing|charge|blame)\b", text.lower()):
            # Do not let inference silently substitute a different suspect.
            return self.packet(NarrationPacket(
                view=build_packet(self.actor.world, self.character).view,
                outcome=NarrationOutcome(
                    action="accuse", accepted=False,
                    detail="That person is not among the listed suspects.",
                ),
            ), narrate=True)
        # A model may suggest a public option but cannot execute arbitrary commands.
        # Known deterministic inputs continue to run without inference.
        # Preserve the existing reliable parser, especially button commands.
        # Only ask the model when deterministic parsing cannot resolve intent.
        known_movement = re.match(
            r"^(?:go to|move to|travel to|walk into|walk to|go|move|travel|enter|visit) ",
            text.strip().lower(),
        )
        if (
            self.ai is not None
            and known_movement is None
            and resolve_intent(self.actor.world, text).status != "resolved"
        ):
            proposed = self.ai.propose(text, self._ai_options())
            if proposed is not None:
                text = proposed
        normalized = re.sub(r"[^a-z0-9\s-]", " ", text.lower())
        normalized = " ".join(normalized.split())
        movement = re.fullmatch(
            r"(?:go to|move to|travel to|walk into|walk to|go|move|travel|enter|visit) (.+)",
            normalized,
        )
        if movement:
            destination = re.sub(r"^(?:the|a|an) ", "", movement.group(1))
            places = {
                entity.get_component(ArchivePlaceComponent).place_key: entity
                for entity in self.actor.world.query()
                .with_all([ArchivePlaceComponent]).execute_entities()
            }
            matches = [
                entity for key, entity in places.items()
                if destination in {
                    key.replace("-", " "),
                    entity.get_component(ArchivePlaceComponent).name.lower().removeprefix("the "),
                }
            ]
            if len(matches) != 1:
                outcome = NarrationOutcome(
                    action="move", accepted=False,
                    detail="Unknown location." if not matches else "Ambiguous location.",
                )
            else:
                target = matches[0]
                world = self.actor.world
                current = container_of(world.get_entity(self.character))
                if current == target.id:
                    outcome = NarrationOutcome(
                        action="move", accepted=True, detail="You are already here.",
                    )
                else:
                    if current is not None:
                        world.get_entity(current).remove_relationship(Contains, self.character)
                    target.add_relationship(
                        Contains(mode=ContainmentMode.ROOM_CONTENT), self.character
                    )
                    outcome = NarrationOutcome(
                        action="move", accepted=True,
                        detail="You enter " + target.get_component(ArchivePlaceComponent).name + ".",
                    )
            return self.packet(NarrationPacket(
                view=build_packet(self.actor.world, self.character).view, outcome=outcome
            ), narrate=True)

        resolved = resolve_intent(self.actor.world, text)
        if resolved.status != "resolved":
            return self.packet(NarrationPacket(
                view=build_packet(self.actor.world, self.character).view,
                outcome=NarrationOutcome(action=resolved.command_type or "",
                                         accepted=False, detail=resolved.reason),
            ), narrate=True)
        ctx = HandlerContext(world=self.actor.world, epoch=self.actor.epoch)
        result = perform(
            ctx, character_id=str(self.character), controller_id=str(self.controller),
            controller_generation=self.generation, resolution=resolved,
            apply=apply_handler_result,
        )
        return self.packet(build_packet(self.actor.world, self.character, result,
                                        action=resolved.command_type or ""), narrate=True)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    game = DemoGame()
    lock = Lock()

    class Handler(BaseHTTPRequestHandler):
        def _json(self, payload: dict[str, object], status: int = 200) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/api/investigation":
                with lock:
                    self._json(game.packet())
                return
            files = {"/": "index.html", "/index.html": "index.html",
                     "/app.js": "app.js", "/style.css": "style.css"}
            if path not in files:
                self.send_error(404)
                return
            file = WEB_ROOT / files[path]
            if not file.is_file():
                self.send_error(404, "Client files not found")
                return
            data = file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", {".html": "text/html", ".js": "text/javascript",
                                               ".css": "text/css"}[file.suffix] + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/api/investigation/actions":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 4096:
                    self._json({"error": "Invalid request size"}, 400)
                    return
                body = json.loads(self.rfile.read(length))
                text = body.get("text")
                if not isinstance(text, str):
                    self._json({"error": "Expected text string"}, 400)
                    return
            except (ValueError, TypeError, json.JSONDecodeError):
                self._json({"error": "Invalid JSON"}, 400)
                return
            with lock:
                self._json(game.act(text))

    print(f"Rabbit Hole Archives demo: http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    serve()
