# Slice 5 browser client (integration scaffold)

Open `index.html` through a static HTTP server (for example `python -m http.server 5173 --directory web`).

**Not yet a playable demo:** this client expects a trusted local backend to implement:

- `GET /api/investigation` → `NarrationPacket` JSON (`view` and optional `outcome`).
- `POST /api/investigation/actions` with `{"text":"examine ..."}` → updated `NarrationPacket`.

The backend must own the Bunnyland world, investigator identity, command dispatch and mutation application. Never expose the authoring fixture, full ECS snapshot or sealed solution to this client. Configure CORS only for the local UI origin. The scene and casebook currently display the restricted projection as JSON pending a typed view renderer.

This is an intentionally small integration checkpoint, not evidence that end-to-end gameplay is complete.
