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
The demo also includes authored public descriptions of each room and its
visible witnesses. Try `what does Porter Quill look like?` in the Study or
`what does Rosalind look like?` after entering the Hall. These appearance
answers are read-only and cannot reveal details from another location.
The scene panel also displays appearances of people physically present, using
the same public description packet; no remote-witness biography is included.


Scene inquiries describe only the current location and visible targets; casebook
inquiries repeat only recorded observations and statements. After you interview a\nwitness, try `what did Quill say about the receipt?` or `what did Rosalind\nsay about the glove?` to revisit matching testimony. This reads the existing\ncasebook and never generates new claims from an NPC. Questions about
unknown or sealed details return an uncertainty response rather than invented
answers. Inquiry does not move the player or discover new evidence, and works
without Ollama.

To ask a focused question, try `ask Quill about the receipt` or `question\nQuill regarding the receipt`. The Narrator displays only matching authored\ntestimony for that topic, while the casebook still records the witness's\ncanonical account. If the account does not address the topic, the Narrator\nsays so rather than inventing an answer.\n\nInterviews can also acknowledge an explicit player approach, for example
`I cautiously ask Quill what he heard` or `I softly ask Rosalind`.
The resulting Narrator cue describes **the investigator's own demeanor** only.
It never changes testimony, NPC state, evidence or outcome; ambiguous
descriptions simply use the usual Narrator prose.

An unsuccessful accusation does not reveal whether the suspect was wrong or the evidence insufficient. Interviewing witnesses is optional but provides useful leads.

### Authoring public narrative details

Case authors may add optional `description` text to each `locations[]` entry
and optional `appearance` text to each `witnesses[]` entry in schema v2.
These are public descriptive facts—not investigation discoveries. On import,
the ECS holds the canonical values, and the Narrator projection includes only
the current room's description and the appearances of witnesses present there.
Cases without either field remain valid; no solution, event, or undiscovered
evidence text is projected. The Missing Seal now authors these details in
`demo_case.json` rather than in a separate data file.

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

The Narrator cycles through three reviewed atmospheric beats for repeated
actions in each scene. This variation works offline and doesn't change the
casebook, recorded testimony, clues, or verdicts. The model still only chooses
tone; it cannot supply new narrative content or override the current action.

The Narrator now combines tone with an **authored, scene-specific atmospheric
beat** for travel, inspection, witness interviews and accusations. These beats
also work without Ollama. When AI is configured, the model may select the
tone and, optionally, a focus ID for a public detail already recorded or a
witness physically present. The server renders only an approved sentence for
that exact ID; a model's own narrative text is ignored. All actual observations,
testimony, and verdicts continue to come from the game engine. We deliberately do not allow
the model to invent facts or produce unrestricted narrative prose in this
first slice. Model calls are synchronous and may delay actions when the local
model is slow or unavailable (8-second timeout per call).

The AI tests use mocked model replies and run with no Ollama installation.
Run `uv run pytest tests/test_local_ai.py` and the full existing test suite
before merging.

## Transcript navigation

The in-page transcript keeps chronological order for reading and exported files.
It sits in a separate, keyboard-focusable scroll area; use **Jump to latest** to
return to the newest messages. New entries follow automatically only while
you're already reading the end of the transcript. Reviewing older entries
doesn't move your scroll position. The **Jump to latest** button shows a count\nof unseen entries until you scroll back to the end or activate it.

For a manual keyboard and screen-reader check: tab to the transcript region,
scroll it with the keyboard, submit another command while reviewing older
messages, and confirm the scroll position is preserved. Activate **Jump to
latest** and confirm the newest entry is visible without moving keyboard focus
away from the button. Confirm result announcements are concise and the exported
file remains in chronological order. Perform browser/AT testing before treating
this feature as accessibility-verified.

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
