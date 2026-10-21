# Play the local Rabbit Hole Archives demo

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). From the repository root:

```sh
uv sync --locked
uv run python -m bunnyland_archives.demo_server
```

Open **http://127.0.0.1:8000/** in your browser. The investigation opens automatically and shares the server's origin.

## The Missing Seal

A treasured seal is missing. Explore the **Study** and **Hall**, interview Porter Quill and Maid Rosalind, and examine the receipt and discarded glove. Halloran looks suspicious, but an accusation only succeeds when you identify the culprit **and** have recorded both supporting clues.

You can use the accessible action buttons or type commands:

- `talk to porter`
- `examine receipt`
- `go to hall`
- `talk to maid`
- `examine glove`
- `accuse ada`

An unsuccessful accusation does not reveal whether the suspect was wrong or the evidence insufficient. Interviewing witnesses is optional but provides useful leads.

## Verify locally

```sh
uv run pytest tests/test_authoring.py tests/test_demo_server.py
uv run pytest
uv run ruff check .
uv run mypy packages/engine/src packages/plugin/src tests
```

Then play through the case in the browser with mouse and keyboard, including one premature accusation and one complete accusation. Check visible focus, tab sequence, and casebook updates; run axe-core and manual screen-reader checks before treating accessibility as verified. **These commands are instructions, not claims that the checks have passed.**

## Limitations

This is a localhost-only single-player development demo using real Bunnyland ECS components and action handlers. No LLM or API key is required. The browser receives restricted investigation packets, never sealed case data or world snapshots.

The server has one shared in-memory session, reset on restart; no save/resume or individual profiles. Movement is a local demo operation rather than a registered Bunnyland movement action, and action plans apply synchronously rather than through full actor tick dispatch. The initial mystery is a tiny proof of interaction, not a finished narrative case. Do not publicly deploy this server.
