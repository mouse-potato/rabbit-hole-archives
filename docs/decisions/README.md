# Architecture Decision Records

These ADRs explain **why earlier decisions were made**, not requirements that must be preserved at all costs. Revisit, amend, or supersede a decision when implementation or playtesting provides better evidence. Prefer a small code change and a focused test over creating an ADR for every gameplay or UI choice.

- [ADR-001 — Reusable engine and standalone game](0001-engine-and-game.md)
- [ADR-002 — ECS-native canonical case truth](0002-ecs-native-case-truth.md)
- [ADR-003 — Privileged case import and the meaning of "sealed"](0003-trusted-import-and-sealing.md)
- [ADR-004 — Neutral accusation verdicts](0004-neutral-accusation-verdicts.md)
- [ADR-005 — Narration receives a packet, not the world](0005-narration-boundary.md)
- [ADR-006 — Witness questions unlock individual statements](0006-statement-level-testimony.md)

**Accepted** = current approach, revisitable; **Proposed** = undecided; **Superseded** = replaced or retired. A game-design choice such as accusation feedback can be changed after playtesting; its ADR captures the previous reasoning, not a permanent mandate.

Only write or update an ADR when the rationale will materially help future contributors. Ground claims about Bunnyland in source or tests, and mark unverified assumptions clearly. Track actionable work in GitHub issues and PRs, not in parallel planning documents.

