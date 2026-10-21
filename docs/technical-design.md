# Rabbit Hole Archives — Current technical overview

> **North star:** Discover a truth that already exists, not invent one as the player investigates.

This is a **working description of the implementation and its guardrails**, not a binding roadmap. Code and tests are the source of truth for behavior; [ADRs](decisions/README.md) preserve rationale and can be revisited. GitHub issues and PRs track upcoming and completed work.

## Near-term goal

Make one **playable, understandable browser investigation**: explore, interview, discover clues, maintain a casebook, and make an evidence-backed accusation. Judge the experience by a complete player playthrough, not by the number of architectural milestones. Procedural case generation, sophisticated AI narration, production hosting, and richer simulation are not prerequisites for this demo.

## Existing boundaries

- **Case authoring:** `packages/engine/src/rabbit_hole_engine` validates structured, versioned case definitions. Authoring data seeds the runtime; it is not a second mutable truth database.
- **Runtime:** `packages/plugin/src/bunnyland_archives` uses a pinned Bunnyland ECS world for canonical case facts and mutable investigation state. Canonical history, evidence provenance, and the solution are distinct from discoveries and statements recorded by an investigator.
- **Actions:** deterministic handlers perform examination, witness questioning, and accusation; player intent resolves to validated actions. Correctness is tested without a model. The current demo host can apply handler mutation plans synchronously; that is not proof of full asynchronous actor tick dispatch.
- **Narrator/client boundary:** restricted view and outcome packets expose only information appropriate for the player or Narrator. The client must never receive a raw world snapshot, sealed solution, or undiscovered clue content. The Narrator does not author or mutate canonical history.
- **Persistence:** Bunnyland save/load has been exercised for the supported investigation state; this does **not** imply the local browser demo provides save/resume or individual sessions.

These boundaries describe useful existing behavior, not a requirement to expand Bunnyland integrations before shipping a local playthrough.

## Critical invariants

1. The case solution and canonical facts do not change in response to ordinary gameplay or narrated improvisation.
2. Discovery and testimony reflect the investigator's access and actions; incorrect player theories may be recorded without changing the underlying truth.
3. Unknown, unreachable, or invalid actions fail without granting information or discovery.
4. The browser and Narrator receive explicit, restricted projections, never the canonical world or privileged save file.
5. Repeated examination must not duplicate discoveries; game rules remain deterministic and testable without LLM calls.

**Security limitation:** ECS is **not** an access-control sandbox. Code holding an in-process world reference can read or change canonical data. Sealing is enforced at the projection boundary and through trusted code plus tests, not by assuming ECS itself protects secrets. See [ADR-003](decisions/0003-trusted-import-and-sealing.md).

## Reference material, not near-term blockers

- [Bunnyland integration](bunnyland-integration.md) — pinned upstream revision, validated plugin/action/persistence behavior, remaining integration limitations and license considerations.
- [HTTP boundary spike](http-boundary.md) — experimental findings about Bunnyland's addon HTTP routing. These findings do **not** prescribe the localhost demo transport.
- [ADRs](decisions/README.md) — historical design reasoning, including the accusation feedback and Narrator packet contracts.
- [Visual style guide](design/visual-style-guide.md) — presentation direction.

For the current browser-demo work, see its PR and `web/README.md`. Test and browser-playthrough results should be recorded on that PR. Do not create another parallel milestone checklist.
