# ADR-003: Privileged case import and the meaning of "sealed"

- Status: **Accepted**
- Date: 2026-10-21

## Context

Canonical case facts and mutable investigation state both live in Bunnyland ECS
(ADR-002). ECS components are readable by every holder of a `World` reference, so storing
the solution in ECS does not by itself hide it, and any plugin with a world reference could
in principle write to any component.

We still need a defensible answer to two questions: who may write canonical facts, and
what does it mean for a clue or solution to be sealed?

## Decision

1. **One privileged writer.** `bunnyland_archives.case_import.import_case` is the only
   code path that creates canonical components. It takes an already validated
   `CaseDefinition`, materializes it once per case key, and refuses duplicates. It is not
   exposed as an action, MCP tool, Narrator tool, or client route.
2. **Sealing is a projection property.** "Sealed" means no projection we emit contains the
   fact. `narrator_view` returns only discovered evidence plus safe case/place metadata; it
   never includes event text, the solution, or unexamined clues. This is enforced and
   tested in our code.
3. **Gameplay mutates only discovery state.** The examination handler's mutation plan
   touches discovery entities and edges. Tests assert that a canonical snapshot is
   byte-identical before and after examination, repeated examination, and travel.
4. **No sandbox claim.** We do not claim ECS access rules protect sealed facts. An
   out-of-process client or Narrator must receive only projections, and a future design
   that requires cryptographic secrecy needs facts outside that process.

## Consequences

- Canonical immutability is a property of our code plus tests, not of the engine. A future
  plugin or contributor that writes canonical components from gameplay would break it;
  review must treat that as a correctness bug.
- The Narrator adapter is restricted to `ArchiveNarratorView`, so narration cannot invent
  or reveal canonical facts through our interface.
- Solvability and spoiler tests can assert on projections directly.
- If an attacker can run arbitrary in-process code, sealed facts are readable. That is
  documented as a trust boundary rather than disguised as access control.
