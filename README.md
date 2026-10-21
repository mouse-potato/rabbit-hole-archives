# rabbit-hole-archives

The Rabbit Hole Archives is an AI narrated murder mystery game based on the [bunnyland.dev](https://bunnyland.dev) framework. RHA is about discovering a truth that already exists, not inventing one as you go.

## Layout

- `packages/engine/src/rabbit_hole_engine` — strict, versioned case-authoring schema and validation (no Bunnyland dependency).
- `packages/plugin/src/bunnyland_archives` — out-of-tree Bunnyland plugin: canonical case components, privileged import, deterministic examination action, restricted Narrator projection.
- `docs/` — technical design, ADRs, and the pinned Bunnyland integration notes.

## Development

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). The dev environment installs a
pinned upstream Bunnyland revision from `uv.lock`.

`.python-version` pins the interpreter to 3.12, so plain `uv sync` selects it even when a
newer Python is installed. CI additionally passes `--python 3.12` explicitly.

```sh
uv sync --locked
uv run pytest          # expect 89 passed
uv run ruff check .    # expect All checks passed!
uv run mypy packages/engine/src packages/plugin/src tests   # expect Success, 16 files
```

Load the plugin into a Bunnyland world with `bunnyland serve --plugin bunnyland.archives`; the
`bunnyland.plugins` entry point in `pyproject.toml` exposes `bunnyland_plugins()`. The plugin
is opt-in (`default_enabled=False`) and registers nothing until requested. Case import is
privileged in-process code; see `docs/bunnyland-integration.md` before wiring it into a
server entrypoint.
