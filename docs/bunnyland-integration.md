# Bunnyland integration: pinned revision and trust boundary

Status: **Slices 2 (M1 ECS integration) and 3 (persistence round-trip) implemented
2026-10-21.** This note records what is actually verified, what is only assumed, and where
the trust boundary sits.

## Pinned upstream revision

| Field | Value |
| --- | --- |
| Repository | `thalismind/bunnyland-server` |
| Distribution name | `bunnyland` (import package `bunnyland`) |
| Version | `1.0.0` |
| Commit | `87824d3c56a32ad91c522dbc242939b11592af05` ("Qualify addon media URLs") |
| Requires | Python >=3.12, `relics-ecs>=0.1.1,<0.2` |
| License | AGPL-3.0-or-later |

The pin lives in `pyproject.toml` under `[dependency-groups].dev` and is resolved into
`uv.lock`, so CI installs exactly this commit. Do not replace it with a floating branch.

Upgrade procedure: change the commit in `pyproject.toml`, run `uv lock`, run
`uv run pytest` (36 tests), and record here what changed upstream. Anything that weakens
the invariants below is a review-worthy change, not a routine bump.

### What this pin verified (source-inspected and executed)

- Out-of-tree modules expose `bunnyland_plugins() -> list[Plugin]` and load via
  `bunnyland serve --module bunnyland_archives`.
- `Plugin`/`EcsContribution`/`CommandContribution` field names used here match
  `src/bunnyland/plugins/model.py` at this commit.
- `apply_plugins` registers contributed components, edges, action definitions, handlers,
  and typed events into `PluginRegistry` and the `WorldActor`.
- `WorldActor.submit` accepts `examine-evidence` through the real submission chokepoint.
- Handler contract is `can_handle` / `execute` returning `HandlerResult` with a
  `MutationPlan`; applying that plan is `execute_mutation_plan`.

### Verified by slice 3 (persistence)

- `save_world`/`load_world` round-trip canonical components, provenance edges,
  investigator session state, and discovery records using Bunnyland's own serializer; there
  is no parallel JSON implementation.
- Entity identifiers are stable across the round-trip, so discovery → investigator and
  discovery → evidence references survive.
- Re-examining after reload is still idempotent, and new discoveries after reload are
  recorded once.
- The Narrator projection is byte-identical before and after a round-trip.
- The save file itself contains sealed facts (solution and event text). It is a privileged
  artifact: do not ship it to a client or treat it as player-facing data.

### Still unverified

- Full asynchronous tick dispatch of an examination (tests apply the handler's plan
  directly, the same level Bunnyland's own handler tests use).
- Whether any other Bunnyland plugin can mutate components it does not own; the
  immutability guarantee below is enforced by our code and tests, not by ECS.
- Player/casebook notes: no note capability exists yet, so nothing about notes round-trips.
- Mapping from snapshot storage to a casebook surface (slice 4).

## Trust boundary

**Trusted in-process code** (may read and write everything):

- `bunnyland_archives.case_import` — the only writer of canonical components.
- `bunnyland_archives.projection` — reads canonical facts, emits a restricted view.
- Action handlers — read canonical facts, write only discovery state.

**Untrusted**: player intent, Narrator output, client payloads, MCP tool arguments. They
may only propose an action; the handler decides. Narration receives
`ArchiveNarratorView`, never a `CaseDefinition` or ECS components.

### Invariants this slice claims

1. Canonical case facts enter a world only through `import_case`, and only once per case
   key.
2. Gameplay examination never emits a mutation targeting a canonical component; the
   tests compare a full canonical snapshot before and after.
3. An examination returns the authored observation verbatim and is idempotent: repeats
   return the same text and create no second discovery record.
4. Unreachable evidence is rejected and records nothing.
5. `narrator_view` contains only discovered evidence plus safe case/place metadata; it
   never contains event text, the solution, or unexamined clues.

### Explicit non-claim

ECS is **not** a security sandbox. Any component in a world is readable by any code with a
`World` reference, so "sealed" here means "our projections never include it", not "the
data is cryptographically hidden". A future out-of-process client must get sealed facts
out of its process entirely; that is a slice-5+ design question, not something ECS access
rules currently provide.

## Package layout

```
packages/engine/src/rabbit_hole_engine/   authoring schema + validation (no Bunnyland)
packages/plugin/src/bunnyland_archives/   out-of-tree Bunnyland plugin (imports engine)
tests/                                    LLM-free engine + integration tests
```

Both modules currently ship in one distribution (`rabbit-hole-engine`). Splitting into two
distributions is deferred until a second consumer needs the engine alone (ADR-001).
