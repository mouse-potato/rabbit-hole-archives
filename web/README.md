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

## Optional local AI (Ollama)

The existing deterministic demo is still the default and requires no model.

To enable experimental AI-assisted command interpretation and safe narration, start
[Ollama](https://ollama.com/) locally, install a chat model (for example,
`ollama pull qwen2.5:3b`), and set its name before launching the game:

```powershell
$env:RHA_OLLAMA_MODEL = "qwen2.5:3b"
uv run python -m bunnyland_archives.demo_server
```

Ollama is contacted **only** at `http://127.0.0.1:11434/api/chat`; no
credentials or browser-side secrets are involved. Unset the variable to
return to deterministic mode:

```powershell
Remove-Item Env:RHA_OLLAMA_MODEL
```

Freeform requests that the deterministic parser cannot resolve may be proposed
as **one** of the currently available actions. The engine still validates
target reachability, evidence visibility, and accusation outcomes. Invalid,
unavailable, or malformed model responses fall back to the deterministic
parser and can be rejected. Ordinary known commands keep their deterministic
behavior. This is **not** freeform, topic-specific NPC dialogue yet.

The local model can also select a tone for one short Narrator line; that line
comes from fixed, trusted templates. All actual observations, testimony, and
verdicts continue to come from the game engine. We deliberately do not allow
the model to invent facts or produce unrestricted narrative prose in this
first slice. Model calls are synchronous and may delay actions when the local
model is slow or unavailable (8-second timeout per call).

The AI tests use mocked model replies and run with no Ollama installation.
Run `uv run pytest tests/test_local_ai.py` and the full existing test suite
before merging.

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
