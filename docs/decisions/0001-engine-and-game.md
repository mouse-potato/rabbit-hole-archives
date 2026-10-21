# ADR-001: Reusable detective engine and standalone game

- Status: **Accepted**
- Date: 2026-10-20

## Context

Rabbit Hole Archives should be a curated detective game, while the detective mechanics should also be reusable by third-party Bunnyland worlds and future case generators.

## Decision

Build an out-of-tree Bunnyland detective plugin with a separately owned standalone game/client. Keep both in one repository initially, with separable packages and a one-way dependency from the game to the engine. Do not modify or fork Bunnyland unless an integration spike shows it is necessary.

## Consequences

- Engine mechanics remain testable independent of game UI and LLM services.
- Curated cases and branding do not leak into reusable core mechanics.
- Initial development avoids premature multi-repository dependency/release overhead.
- Exact package layouts and frontend framework remain open.
