# ADR-002: ECS-native canonical case truth

- Status: Accepted
- Date: 2026-10-20

## Context

The game requires a fixed history and solution alongside mutable discoveries and player notes. Keeping an additional runtime truth database risks inconsistencies.

## Decision

Use Bunnyland ECS as the single authoritative runtime representation of canonical case facts and mutable investigation state. Structured case files can initialize ECS but will not operate as a competing runtime truth service.

The Narrator is a non-authoritative consumer of scoped projections and a requester of validated actions.

## Consequences

- Reuses Bunnyland persistence and ECS conventions.
- Requires explicit distinction between objective facts, character beliefs, and investigator discoveries.
- We must verify concrete read access and write protection mechanisms during the first integration spike.
- Case initialization needs a privileged path distinct from gameplay.
