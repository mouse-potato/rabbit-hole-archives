# Slice 5 HTTP boundary: what the pinned Bunnyland actually provides

Status: spike completed 2026-10-21 against `thalismind/bunnyland-server@87824d3`.

The open slice-5 question was whether the client can be a browser app without inventing a
server stack, and whether the sealed-fact boundary survives the move out of process
(ADR-003). This records what was executed, not what the plugin docs claim.

## Corrections to earlier documentation

Two statements were carried in `README.md`, `docs/technical-design.md`,
`docs/bunnyland-integration.md` and the plugin docstring and were **false** at this pin:

1. **There is no `--module` flag.** `bunnyland serve --help` contains zero mentions of
   `module`; `cli.select_plugins` resolves ids through `plugins.loader.discover_plugins()`,
   which reads the `bunnyland.plugins` entry-point group only. There is no module-path
   loader.
2. **Nothing discovered this plugin.** `pyproject.toml` declared no
   `bunnyland.plugins` entry point, so `discover_plugins()` returned 29 builtin plugins and
   never ours. `bunnyland serve --plugin bunnyland.archives` failed with "unknown plugin
   id".

Both are now fixed: the entry point `archives = "bunnyland_archives:archive_plugin"` is
declared, and the plugin is `default_enabled=False` so a non-archive world never gains
detective actions by accident.

Verified by execution after the change:

```sh
uv run python -c "
from bunnyland.cli import build_actor
actor, applied = build_actor(['bunnyland.archives'])
print([p.id for p in applied])"
# ['bunnyland.media', 'bunnyland.prompt_filters', 'bunnyland.archives']
```

## The route contract for an addon server (verified)

`Plugin.runtime.http` takes `HttpContribution(zone=…, registrars=(callable,))`.
`create_app` mounts each registrar's `APIRouter` at
`/v1/{zone}/extensions/{plugin.id}` — for us `/v1/play/extensions/bunnyland.archives` — and
rejects any route whose local path would collide with an absolute or cross-zone
authorization surface. The registrar is called as

```python
registrar(router, actor, *, meta, loop, save_path, definitions_path,
          worldgen_options, plugins, media_store, addon_media, play_websocket_auth)
```

Executed against a real `WorldActor` built by `tests/archive_harness.build_scenario()` and a
real `create_app`:

- `GET /v1/play/extensions/bunnyland.archives/…` → `200` once the request carries
  `X-Bunnyland-Client-Id`; without it the app answers `403 client_id_required`.
- `POST` with a pydantic body → `200`, body round-tripped.
- `OPTIONS` preflight with `cors_origins="http://localhost:5173"` → `200` with
  `access-control-allow-origin` and `x-bunnyland-client-id` in the allowed headers, so a
  Vite dev server can talk to it.
- No token store, claims, or user credentials are needed when the app is created with
  `allow_unauthenticated_embedding=True`; the whole `/v1/…/claims` machinery stayed unused.

## Consequences for the slice-5 design

- **We do not need `bunnyland serve`.** That command generates a world with an LLM, sets up
  character models, moderation, auth and claims — none of which a curated case wants. We
  can host `create_app` ourselves around an imported case and still use the real server,
  real action dispatch, and the sanctioned addon route zone.
- **The sealed boundary holds by construction.** The browser gets only what our registrar
  serialises from `narrator_view` / `build_packet`. No projection is sent wholesale.
- **`fastapi`, `uvicorn` and `httpx` are not dev dependencies** and had to be supplied for
  the spike. The client milestone adds them as an optional `server` extra so the
  LLM-free test suite keeps running without them.
- **Our extension routes are not origin-guarded for us.** `create_app` applies trusted-origin
  checks to its own `/v1/play` routes, but an addon route only gets CORS headers; a `POST`
  with a foreign `Origin` was accepted (`200`). Fine for a loopback single-player app; a
  deliberate origin check belongs in our registrar before this is exposed beyond localhost.

## Still unverified

- Whether `bunnyland serve --plugin bunnyland.archives` completes a full run: the plugin is
  now discoverable and applies through `build_actor`, but `serve` additionally generates a
  world with a model, which is irrelevant to a curated case and was not exercised.
- Asynchronous tick dispatch of an archive action through `WorldActor.submit` inside the app
  loop. The handlers still receive plans that the caller applies; M1's dispatch gap is
  unchanged by this spike.
