# Contributing and development workflow

This is an early project convention document, adapted from practices used on Pretty Little Stitches. Update concrete commands when packages and CI are scaffolded.

## Branches and reviews

- Work on a focused feature, fix, docs, or spike branch; do not develop features directly on `main`.
- Open a GitHub pull request for review before merging. Keep PRs small and tied to an issue or clear acceptance criteria.
- Prefer descriptive branch names (`docs/initial-architecture`, `spike/ecs-boundaries`, `feature/evidence-discovery`).
- Protect `main` with required pull requests and passing checks when CI is established; do not force-push protected branches.
- Use clear PR summaries: what changed, why, how it was tested, and known risks.
- Do not merge failing or unverified changes. Locally review functionality before marking work ready.

## Tests and quality gates

- Comprehensive automated coverage is required for changed behavior. Favor deterministic unit tests for investigation rules, integration tests for Bunnyland action dispatch/persistence, and end-to-end tests for gameplay.
- Case schema and solvability validators require positive and negative fixtures.
- Verify authorization and knowledge boundaries with tests that try to discover and mutate sealed facts illegally.
- For client changes, test keyboard navigation, focus, labels/semantics, and accessible state updates; automate WCAG-oriented checks with Playwright + axe-core when the client exists.
- Do not replace manual accessibility checks with automated scans; include manual keyboard/screen-reader smoke testing for relevant UI changes.
- Run typechecking, tests, and relevant accessibility checks before requesting review. Document exact commands after toolchain selection.
- LLM-backed tests may supplement coverage, but core correctness must pass without LLM calls.
- Never claim a CI check or local test passed unless it actually ran.

## Documentation and decisions

- Keep `docs/technical-design.md` current as assumptions are verified.
- Record consequential architectural choices as ADRs under `docs/decisions/`.
- Include reproducible findings and references for technical spikes.
- Avoid introducing general-purpose abstractions before the first vertical slice proves they are necessary.

## Open setup items

- Confirm licensing and dependency compatibility with Bunnyland's AGPL-3.0-or-later.
- Choose client framework and implement test/CI workflows when packages exist.
- Configure GitHub branch protection after first CI checks are available.
