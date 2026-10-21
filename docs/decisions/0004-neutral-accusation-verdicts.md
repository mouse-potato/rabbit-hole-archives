# ADR-004: Accusation verdicts are neutral in public

- Status: **Accepted**
- Date: 2026-10-21

## Context

A deterministic accusation needs a verdict. The obvious implementation returns three
outcomes: correct, wrong suspect, and right suspect with insufficient evidence. That third
outcome is a spoiler: telling a player "you have the right person but not enough proof"
hands them the solution and removes the deduction.

The alternative — always answering "unproven" — gives no feedback at all and makes the case
feel broken, so some signal is needed.

## Decision

1. The resolver returns two public verdicts: `solved` and `unproven`. A case is `solved`
   only when the named suspect is the culprit *and* every supporting clue has already been
   recorded by that investigator.
2. The privileged record (an ECS component and a private event) also stores `culprit_match`
   and `missing_evidence` so tests, authoring checks, and future tooling can assert exact
   behaviour.
3. No projection exposes those privileged fields. `ArchiveNarratorView` carries a single
   `solved` boolean, so a wrong suspect and a thin case are indistinguishable to a player,
   the Narrator, or a client.
4. Accusations are recorded, not consumed: a rejected accusation costs an action and stays
   in the case history, so a player can accuse again after finding more evidence.

## Consequences

- Players get exactly one bit of feedback (`solved`) plus the narrative framing of their own
  accusation. Repeated guessing is possible but gains nothing, because being right still
  requires the documented evidence.
- Narration cannot use the privileged fields; if a future design wants an "insufficient
  evidence" hint, it must be an authored, non-diagnostic message and it needs its own ADR.
- Tests must assert both layers: `culprit_match` in the event, `solved` in the projection.
- The `unproven` wording is authored narration, not a verdict string, so it can differ per
  case without changing mechanics.
