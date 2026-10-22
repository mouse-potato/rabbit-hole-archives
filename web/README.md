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

You can also ask read-only questions such as `what's in the hall?`,
`look around`, `what do I know?`, or `review my evidence`.
Scene inquiries describe only the current location and visible targets; casebook
inquiries repeat only recorded observations and statements. After you interview a\nwitness, try `what did Quill say about the receipt?` or `what did Rosalind\nsay about the glove?` to revisit matching testimony. This reads the existing\ncasebook and never generates new claims from an NPC. Questions about
unknown or sealed details return an uncertainty response rather than invented
answers. Inquiry does not move the player or discover new evidence, and works
without Ollama.

An unsuccessful accusation does not reveal whether the suspect was wrong or the evidence insufficient. Interviewing witnesses is optional but provides useful leads.

## Optional home-server AI (Ollama)

The deterministic demo needs no model. If you already run Ollama on a shared
home server, **do not download another model** on your PC. Use the model's
existing Ollama tag and the server's LAN hostname or IP. **Both values below are placeholders and must be replaced before running RHA:**

```powershell
$env:RHA_OLLAMA_URL = "http://YOUR_OLLAMA_SERVER_IP:11434"  # REQUIRED: replace placeholder
$env:RHA_OLLAMA_MODEL = "YOUR_INSTALLED_OLLAMA_MODEL"  # REQUIRED: replace placeholder
uv run python -m bunnyland_archives.demo_server
```

The default URL, if unset, is `http://127.0.0.1:11434`. The application
appends `/api/chat`; provide **only the server origin**, not the API path.
Only trusted server-side environment configuration can choose the endpoint.
The browser continues talking solely to Rabbit Hole Archives on localhost.

The home server must be reachable from this PC, its Ollama API must be
listening on an interface accessible from your LAN, and any firewall must
permit that connection. You can check connectivity from PowerShell with:

```powershell
Invoke-RestMethod "$env:RHA_OLLAMA_URL/api/tags"
```

An ordinary LAN HTTP connection is **unencrypted**, so use a trusted home
network or an HTTPS/private-tunnel endpoint. Do not expose an unauthenticated
Ollama API directly to the public internet. Only public investigation options
and already-approved outcomes are sent to the configured model, not sealed
case facts. The server does not send a browser token or game credentials.

To return to offline mode, stop the demo server, then:

```powershell
Remove-Item Env:RHA_OLLAMA_MODEL
Remove-Item Env:RHA_OLLAMA_URL
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


### Troubleshooting optional AI

To see *why* the optional local model did not help with a request, enable
server-console diagnostics before launching the demo:

```powershell
$env:RHA_AI_DEBUG = "1"
uv run python -m bunnyland_archives.demo_server
```

The server prints small status labels such as `intent: validated_action`,
`intent: target_not_available`, `intent: connection_or_timeout_failure`,
`intent: invalid_model_response`, or `narration: invalid_tone_using_neutral`.
Logs deliberately omit the player request, generated text, evidence, model
response body, and server URL. They are emitted **only to the server console**,
not sent to the browser. This opt-in is intended for development; unset
`RHA_AI_DEBUG` when finished. If there is no diagnostic for an action, it may
have been handled deterministically without an Ollama call.

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
