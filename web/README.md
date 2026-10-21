# Play the local Rabbit Hole Archives demo

Requires Python 3.12 and uv. From the repository root:

```sh
uv sync --locked
uv run python -m bunnyland_archives.demo_server
```

Open **http://127.0.0.1:8000/** in your browser. The client connects automatically and shares the same origin as the server.

## The Missing Seal

You are investigating a missing seal in a two-room house. Explore the Study and Hall, question Porter Quill and Maid Rosalind, inspect the available evidence, and accuse someone once you have a theory.

Use the on-screen buttons or enter commands such as:

- `talk to porter`
- `examine receipt`
- `go to hall`
- `talk to maid`
- `examine glove`
- `accuse ada`

The local server uses the original micro-case and actual Bunnyland ECS components and action handlers. No LLM or API key is needed. The browser receives only a restricted investigation projection, public outcomes, and safe available-action metadata. It never receives the case's solution or save snapshots.

**Development limitations:** one shared in-memory session, reset on server restart; no save/resume or individual player profiles. Movement is currently a privileged local demo operation (not a Bunnyland action-dispatch command), and handler plans run synchronously rather than through asynchronous actor ticks. The initial case is intentionally tiny. Browser end-to-end, axe-core, and manual screen-reader verification remain necessary.
