<div align="center">

![Rabbit Hole Archives — Some questions lead further down](docs/design/references/readme-header.png)

</div>

# Rabbit Hole Archives

**Some questions lead further down.**

Rabbit Hole Archives is an AI-assisted detective mystery game built on the [Bunnyland](https://bunnyland.dev) framework. Investigate a case, question witnesses, examine evidence, and make your accusation. The truth of each mystery is established in advance: the Narrator can help you explore it, but cannot rewrite it.

## Play the demo

The first playable mystery, **The Missing Seal**, runs in your browser on a local development server. You'll investigate two rooms, interview witnesses, and assemble evidence before accusing a suspect.

Requires **Python 3.12** and [uv](https://docs.astral.sh/uv/). From the repository root:

```sh
uv sync --locked
uv run python -m bunnyland_archives.demo_server
```

Open **http://127.0.0.1:8000/** to play. No AI model is required: the demo works with deterministic commands and action buttons.

To try AI-assisted natural-language commands and constrained narration, connect an existing Ollama model on your PC or home server. See the [demo setup guide](web/README.md) for configuration, limitations, and playtesting instructions.

## Project structure

- `packages/engine/src/rabbit_hole_engine/` — versioned mystery definitions and validation.
- `packages/plugin/src/bunnyland_archives/` — Bunnyland integration, investigation mechanics, and the Narrator boundary.
- `web/` — browser demo and its local setup guide.
- `tests/` — mechanics, persistence, intent, and demo regression tests.
- `docs/` — design notes, visual references, technical decisions, and integration details.

## Development

Install dependencies with `uv sync --locked`, then run the checks from the repository root:

```sh
uv run pytest -q
uv run ruff check .
uv run mypy packages/engine/src packages/plugin/src tests
```

The demo is a **localhost-only, single-player development prototype**, not a public deployment. Its investigation state resets when the server restarts. See [web/README.md](web/README.md) for manual playtesting and accessibility checks.
