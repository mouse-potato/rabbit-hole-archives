# rabbit-hole-archives

The Rabbit Hole Archives is an AI narrated murder mystery game based on the [bunnyland.dev](https://bunnyland.dev) framework. RHA is about discovering a truth that already exists, not inventing one as you go.

## Layout

- `packages/engine/src/rabbit_hole_engine` — strict, versioned case-authoring schema and validation (no Bunnyland dependency).
- `packages/plugin/src/bunnyland_archives` — out-of-tree Bunnyland plugin: canonical case components, privileged import, deterministic examination action, restricted Narrator projection.
- `docs/` — technical design, ADRs, and the pinned Bunnyland integration notes.

## Development

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). The dev environment installs a
pinned upstream Bunnyland revision from `uv.lock`.

```sh
uv sync --locked
uv run pytest
uv run ruff check .
uv run mypy packages/engine/src packages/plugin/src tests
```

Load the plugin into a Bunnyland world with `bunnyland serve --module bunnyland_archives`
(the module exposes `bunnyland_plugins()`). Case import is privileged in-process code; see
`docs/bunnyland-integration.md` before wiring it into a server entrypoint.
