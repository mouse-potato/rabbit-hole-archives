# ADR-005: Narration receives a packet, not the world

- Status: **Accepted**
- Date: 2026-10-21

## Context

The Narrator is an LLM. Technical design decision 5 says it is non-authoritative, and
MVP non-goals exclude letting it invent evidence or decide the solution. A prompt
instruction is not an enforcement mechanism: if the adapter can pass arbitrary world state,
the model can leak or invent canonical facts and only prose review would catch it.

## Decision

1. The Narrator adapter receives exactly one object: `NarrationPacket`, containing the
   restricted projection (`ArchiveNarratorView`) and a `NarrationOutcome` with public
   fields only — an observation, attributed statements, or the neutral verdict.
2. Privileged fields (`culprit_match`, `missing_evidence`, sealed solution, event text,
   undiscovered evidence) never cross that boundary; `build_packet` copies fields
   explicitly rather than serialising events.
3. Player intent is parsed deterministically into one proposed action (`resolve_intent`),
   then executed by the real handler (`perform`). The model never chooses an action
   identifier or a target id; it may only rephrase text that the packet already contains.
4. `perform` does not apply mutation plans by itself. The host decides whether the plan is
   applied inside a tick or in a deterministic test.

## Consequences

- A prompt injection in player text can at most produce an unresolved intent; the handler
  still validates reachability and knowledge scope.
- Narration can be wrong in wording but cannot become canonical truth, and tests assert the
  packet contents directly.
- Adding a new field to narration means adding it to the projection or the outcome type,
  which is a visible review change rather than an accidental widening.
- The final client still needs its own decision on how to render packets; that is separate
  from what the Narrator may know.
