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

If `uv sync` fails while building `pyyaml`, uv picked an interpreter newer than the pinned
3.12 (Python 3.15 on Windows is the usual case): `pyyaml` publishes wheels only up to
cp314, so anything newer falls back to a source build and needs a C toolchain. Run
`uv sync --locked --python 3.12` instead, and delete a stale `.venv` if uv objects to
the existing one.

Load the plugin into a Bunnyland world with `bunnyland serve --module bunnyland_archives`
(the module exposes `bunnyland_plugins()`). Case import is privileged in-process code; see
`docs/bunnyland-integration.md` before wiring it into a server entrypoint.
