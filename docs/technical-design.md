# Rabbit Hole Archives — Technical Design (Working Draft)

Status: **Draft v0.2** · Updated: 2026-10-21

> **North star:** RHA is about discovering a truth that already exists, not inventing one as you go.

This document distinguishes **verified Bunnyland interfaces**, **agreed decisions**, **proposed behavior**, and **open verification work**. It is deliberately incremental, not a finalized specification.

## Product goals

- A text-first investigation with an AI Narrator that narrates and interprets freeform player intent.
- A predetermined, genuinely solvable mystery: solution, historical timeline, clue provenance, and NPC knowledge are canonical.
- Consistent character knowledge, motives, testimony, and possible deception.
- A persistent investigator casebook containing discovered evidence, statements, leads, timelines, and player notes.
- Save/resume that does not depend on retaining the full chat transcript.
- Reusable, structured case definitions supporting curated mysteries first and constrained generation later.

## MVP non-goals

- Procedurally generated mysteries.
- Autonomous NPC routines, continuously advancing time, active threats, or additional crimes.
- Full-featured deduction simulation, elaborate UI, or a catalog of cases.
- Letting the Narrator improvise new canonical evidence, change the culprit, or author world-state mutations.
- Reimplementing Bunnyland's ECS, action dispatch, or persistence.

## Agreed architectural decisions

See [decisions](decisions/README.md).

1. **Hybrid product boundary:** reusable detective plugin + separate standalone game/client.
2. **One repository initially:** keep independently extractable engine and client packages in a monorepo; do not split prematurely.
3. **ECS-native truth:** canonical case facts and mutable investigation state both live in Bunnyland ECS, with distinct authorization boundaries. An authored case file may bootstrap ECS, but is not a second runtime truth store.
4. **Static, player-driven runtime:** the crime is complete at session start; no autonomous NPC changes for MVP.
5. **Narrator non-authority:** the Narrator receives appropriately scoped projections and validated action results. It cannot directly mutate canonical facts or decide a solution.
6. **LLM-independent correctness:** mystery validation, action outcomes, knowledge scope, and persistence must be testable without model calls.

## System boundaries (proposed)

- **Case loader / validator:** imports a schema-versioned, authored case into ECS after checking structure and solvability assumptions. Does not retain a competing mutable case store.
- **Detective ECS plugin:** models evidence, historical events, knowledge/beliefs, testimony provenance, and investigation/discovery state; registers gameplay action definitions, handlers, events, and projections.
- **Trusted action pipeline:** converts player intent into proposed actions, validates eligibility and knowledge scope, then mutates permitted state.
- **Narrator adapter:** narrates from a restricted view and action outputs. Dialogue can vary but must not introduce new authoritative facts.
- **Standalone client:** text interaction and accessible, searchable casebook UI.
- **Persistence:** rely on Bunnyland's persistence where verified; independently confirm that casebook data and canonical state round-trip correctly.

These are conceptual module boundaries, **not** verified Python module paths or callable signatures.

## Verified Bunnyland interfaces (source-inspected)

At review time (2026-10-20), the public `thalismind/bunnyland-server` repository contains:

- Plugin definitions registered through the `bunnyland.plugins` Python entry-point group, and out-of-tree modules loaded using `bunnyland serve --module …`.
- `Plugin`, `DependencyContribution`, `EcsContribution`, `CommandContribution`, `RuntimeContribution`, and `ContentContribution` in `src/bunnyland/plugins/model.py`.
- `EcsContribution` fields: `components`, `edges`, `systems`, `observers`.
- `CommandContribution` fields: `command_types`, `action_handlers`, `action_definitions`, `typed_events`, `action_callbacks`.
- `RuntimeContribution` fields include `service_factories`, `projection_factories`, `perspective_queries`, and zoned HTTP contributions.
- The `neonsim` plugin provides a concrete example of contributing ECS types, handlers, typed events, prompt fragments, and services.
- The `memory` plugin contributes memory-specific actions and factories; this does **not** establish that retrieval-based memory can serve as canonical mystery truth.
- The server requires Python >=3.12 and declares `relics-ecs>=0.1.1,<0.2`; license is `AGPL-3.0-or-later`.

Sources:
- https://github.com/thalismind/bunnyland-server/blob/main/PLUGINS.md
- https://github.com/thalismind/bunnyland-server/blob/main/pyproject.toml
- https://github.com/thalismind/bunnyland-server/blob/main/src/bunnyland/plugins/model.py
- https://github.com/thalismind/bunnyland-server/blob/main/src/bunnyland/simpacks/neonsim/plugin.py
- https://github.com/thalismind/bunnyland-server/blob/main/src/bunnyland/foundation/memory/plugin.py

**Not yet verified:** mutation guards across all write paths; fine-grained secrecy and projection behavior; typed action handler signatures; mapping from snapshot storage to casebook; behavior under zero autonomous ticks; safe serialization of sealed facts.

### Slice 2 update (2026-10-21)

The plugin now pins `thalismind/bunnyland-server` at `87824d3c56a32ad91c522dbc242939b11592af05`
and is exercised against it. See [bunnyland-integration.md](bunnyland-integration.md) for the
pin, the verified interfaces, the remaining gaps, and ADR-003 for the trust boundary.
Verified by execution (not only inspection): out-of-tree module loading contract, component
and edge registration, `WorldActor.submit` acceptance of plugin actions, the
`can_handle`/`execute`/`MutationPlan` handler contract, a full `save_world`/`load_world`
round-trip with stable entity references, and three registered actions
(`examine-evidence`, `talk-to-witness`, `accuse-suspect`) whose behaviour is deterministic
across repeated runs. The snapshot contains
sealed facts by design, so it is treated as a privileged artifact. Still open from the list
above: mutation guards on other plugins' write paths, full asynchronous tick dispatch of an
examination, and casebook notes (no note capability exists yet).

## Conceptual data model (proposed, subject to spike)

| Concept | Canonical or mutable | Example |
| --- | --- | --- |
| Case identity and version | Canonical | Case ID, schema version |
| Historical event | Canonical | Death occurred at 20:00 |
| Evidence and provenance | Canonical | Glass fragment found in study; derived from an earlier event |
| NPC knowledge or belief | Canonical | Witness sincerely believes they saw victim at 21:00 |
| Testimony rules | Canonical | What a witness can disclose, conceal, misremember or lie about |
| Investigation session | Mutable | Current location, visited sites |
| Discovery record | Mutable | Evidence examined, when discovered |
| Casebook entry | Mutable | Recorded statement, lead, player note |
| Accusation/result | Mutable | Player's submitted theory and validation outcome |

Prefer ECS edges for relations such as `evidence -> historical event`, `NPC -> belief`, and `investigator -> discovery` where Bunnyland's ECS semantics make that practical. The names above are **not** promised class names.

## Trust boundaries and invariants

1. At runtime, ECS holds the single authoritative case world; imported authoring files do not become competing truth.
2. Canonical facts cannot change through gameplay or Narrator commands; loading/editing cases is a privileged operation.
3. Player and Narrator views never expose undiscovered evidence or sealed solution facts without explicit entitlement.
4. NPC assertions are records of what an NPC says/believes, **not** automatic statements of objective truth.
5. The casebook can contain incorrect player theories without changing canonical facts.
6. Every gameplay state change is validated and attributable to an action or explicitly defined event.
7. Narrative prose alone is never committed as evidence, and narration must not falsely present unapproved claims as canonical.
8. Save/resume retains discovery and casebook state without relying on conversation context.

**Security caveat:** ECS-native sealed data is an access-control challenge, not a claim that merely storing facts in ECS makes them secret. The initial spike must establish enforceable read/write boundaries.

## First vertical slice: one evidence discovery

A small authored test case has one room, one discoverable clue, and one investigator.

1. Load the case and initialize canonical ECS state.
2. Issue a structured examination action via Bunnyland's action system.
3. Validate access to the clue, return canonical observations, and record a discovery.
4. Project a minimal, safe result for Narrator narration.
5. Show a casebook record independently of chat history.
6. Save/reload and verify idempotent discovery and preserved provenance.

### Acceptance criteria

- Deterministic action returns the same canonical clue facts across runs.
- Invalid or inaccessible examinations do not change discovery state.
- Duplicate examinations do not create duplicate casebook discoveries.
- Narrator-facing results do not include sealed answers or undiscovered clues.
- Canonical components are unchanged after normal actions.
- Persistence round-trip retains discoveries, notes, and stable entity references.
- These checks pass with an LLM-free test harness.

## Follow-on vertical slice (not part of first spike)

Extend to 2–3 locations, 2–3 NPCs, scripted evidence, contradictory testimony, basic lead tracking, and an accusation checked against the predetermined solution. A compact public-domain Sherlock Holmes adaptation is a candidate for first content case; selection and copyright/source edition checks remain open.

## Open technical spikes

1. **Mutation and perspective boundaries:** investigate Bunnyland's actual authorization / projection enforcement. Test direct and indirect write paths and read leaks.
2. **Action & event plumbing:** determine registration contracts and how to execute without autonomous ticks.
3. **Persistence round-trip:** confirm ECS snapshot and casebook lifecycle; version migration behavior.
4. **Case loading / solvability:** choose schema and validate evidence provenance and solution reachability.
5. **Narrator narration safety:** enforce structured action results and scoped dialogue, without trusting prompt text alone.
6. **License and packaging:** assess AGPL obligations for distributed plugin/client; establish dependency version policy.

## Milestones (tentative)

- **M0 Documentation and repository workflow:** design draft, ADRs, branch/PR conventions.
- **M1 ECS boundaries proof:** canonical protected facts, safe projections, deterministic discovery and round-trip.
- **M2 Playable micro-case:** interview, discover, casebook, accusation, resume.
- **M3 Curated demo:** validated public-domain-inspired case and accessible client polish.

Future **Active Threat** simulation should reuse explicitly recorded events and consistent state transitions, but no autonomous behaviors are required for MVP.
