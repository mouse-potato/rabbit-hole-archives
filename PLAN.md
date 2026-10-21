# Implementation plan

Status: execution started 2026-10-20.

Progress:

- **Slice 1 complete (2026-10-20)** — engine package, strict versioned schema, validator
  tests, LLM-free CI. PR #18.
- **Slice 2 complete (2026-10-21)** — Bunnyland plugin wiring, privileged import,
  deterministic examination, canonical-immutability and projection-secrecy tests against
  the pinned upstream commit. Details in `docs/bunnyland-integration.md` and ADR-003.
- **Slice 3 complete (2026-10-21)** — save/reload through Bunnyland's own persistence:
  canonical state, provenance edges, investigator location, and discoveries all survive
  with stable entity references; projections are identical after reload; adversarial tests
  confirm sealed facts stay out of projections while the save file itself is privileged.
- **Slice 4 complete (2026-10-21)** — playable micro-case: schema v2 witnesses and
  attributed testimony, `talk-to-witness` with ordered statements and leads,
  `accuse-suspect` resolved deterministically against the sealed solution, and neutral
  public verdicts (ADR-004). 75 tests. M1 still owes full asynchronous tick dispatch of an
  action; current tests apply the handler's mutation plan directly.
- **Slice 5 next** — standalone client consuming restricted projections plus the Narrator
  adapter (no authoritative narration), keyboard/axe checks, documented accessibility
  limits.

Existing ADRs and technical-design.md are authoritative.

## Sequence and PR boundaries

1. **Authoring foundation** — create the separable Python engine package, strict versioned case schema, positive/negative validator tests and LLM-free CI. Authoring objects are import inputs, never a runtime truth database. Use an original tiny fixture; defer licensed adaptations.
2. **Bunnyland M1 integration** — source-inspect and pin a tested upstream revision; register ECS components and plugin; implement privileged import and deterministic examination through actual action dispatch. Prove inaccessible/duplicate examination behavior and canonical immutability. Explicitly document trusted in-process code vs untrusted player/model boundaries; do not claim ECS is a security sandbox.
3. **Persistence and restricted projections** — round-trip actual Bunnyland snapshots, including notes and discoveries; adversarial tests for sealed solution and undiscovered evidence leakage. No parallel JSON save implementation.
4. **Playable micro-case** — locations, witnesses, attributed testimony, leads and validated accusation, all deterministic and tested without model calls.
5. **Standalone client and narrator adapter** — separate client consuming restricted projections, casebook and accessible text interaction; structured intent validation, keyboard/axe checks and manual accessibility limitations. Narration is non-authoritative.
6. **Demo and release readiness** — complete an original solvable case, end-to-end save/resume, package/license review and runnable setup instructions.

## Acceptance gates

- Each implementation PR states exact test/typecheck commands and remaining integration gaps.
- Never merge PRs automatically; opening PRs is authorized, review remains required.
- Do not substitute a standalone in-memory engine for ECS integration.
- Schema validation checks identity uniqueness, references, clue provenance and declared solution-support reachability. It does not claim to prove human deductive solvability.
- M1 is complete only when the six first-slice acceptance criteria in the technical design pass against real Bunnyland.
- Any unavailable upstream guard is a documented blocker or explicit trusted-service boundary, not a prompt-only security fix.

## Progress reporting

October 21 morning brief: report completed slices, actual test results, PR links, next step and blockers. A private reminder has been recorded. No per-PR notifications requested.
