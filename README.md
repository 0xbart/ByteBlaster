# ByteBlaster

An internal office soundboard. Anyone on the office network can upload and play
mp3/wav files. A click plays the sound on **every connected client**
(WebSocket broadcast). Authentication is implicit via IP address: an unknown IP
claims a username once and stays bound to that IP forever.

## Stack

- **Backend**: FastAPI + SQLAlchemy 2 (async) + asyncpg + Alembic
- **Frontend**: Vue 3 (Composition API) + Pinia + Buefy 3 + Bulma + OpenAPI-generated client
- **DB**: PostgreSQL (Docker)
- **Storage**: local Docker volume

## Quick start (Docker)

```bash
docker compose up --build
# Frontend → http://localhost:8080
# Backend  → http://localhost:8000  (OpenAPI at /openapi.json)
```

The frontend image builds from `./frontend` only and uses the committed
`src/api/schema.d.ts`. Regenerate the schema with
`./scripts/generate-client.sh` after backend OpenAPI changes and commit the
result before building the frontend image.

## Dev workflow

### Option A — everything in Docker (single command, hot reload)

```bash
docker compose -f docker-compose.dev.yml up
# → Frontend (Vite HMR): http://localhost:5173
# → Backend (uvicorn --reload): http://localhost:8000
```

Backend and frontend mount their source from the host; saving files in
`backend/app/**` or `frontend/src/**` triggers an automatic reload.

### Option B — on the host (faster, no Docker for app code)

```bash
# 1) Database
docker compose up -d db

# 2) Backend (host, with hot reload)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
uvicorn app.main:app --reload

# 3) Frontend
cd ../frontend
npm install
npm run generate:client     # generate typed schema against the running backend
npm run dev                  # http://localhost:5173 (proxy /api and /ws → :8000)
```

> **API contract**: every frontend API call **must** go through the generated
> client in `frontend/src/api/`. Do not call `fetch` directly. After backend
> changes: re-run `npm run generate:client`.

## Configuration (env vars, prefix `BYTEBLASTER_`)

| Variable             | Default                                          | Purpose                                              |
|----------------------|--------------------------------------------------|------------------------------------------------------|
| `DATABASE_URL`       | `postgresql+asyncpg://byteblaster:.../byteblaster` | Postgres async DSN                                   |
| `STORAGE_DIR`        | `/data/sounds`                                   | Directory where audio files land                     |
| `MAX_UPLOAD_BYTES`   | `10485760` (10 MB)                               | Max file size                                        |
| `CORS_ORIGINS`       | `["http://localhost:5173"]`                      | Vite dev-server origin (JSON-encoded list)           |
| `TRUSTED_PROXIES`    | `[]`                                             | CIDRs whose `X-Forwarded-For` we trust (JSON list)   |

**Important**: when the backend sits behind a reverse proxy (nginx, traefik),
`TRUSTED_PROXIES` must contain the proxy's subnet — otherwise every user shows
up as the same proxy IP and they share a single account. The default
`docker-compose.yml` trusts the standard Docker private ranges (`172.16/12`,
`10/8`, `192.168/16`).

List-type env vars (`CORS_ORIGINS`, `TRUSTED_PROXIES`) are parsed as JSON,
not CSV. Example: `'["172.16.0.0/12","10.0.0.0/8"]'`.

## WebSocket protocol (`/ws`)

No subprotocol; no client messages expected. The server emits JSON events:

```json
{ "type": "play", "sound_id": 42, "sound_url": "/api/sounds/42/file",
  "display_name": "Airhorn", "by": "Alice", "at": "2026-05-15T10:11:12Z" }

{ "type": "sound_added",   "sound": { /* SoundOut */ } }
{ "type": "sound_updated", "sound": { /* SoundOut */ } }
{ "type": "sound_removed", "sound_id": 42 }
{ "type": "tag_removed",   "name": "fun" }
{ "type": "tag_renamed",   "id": 3, "old_name": "fun", "new_name": "funny" }
{ "type": "category_renamed", "id": 1, "new_name": "FX" }
{ "type": "presence",      "users": [ /* PresenceUser[] */ ] }
```

WebSocket auth uses the same IP mechanism as REST. Unknown IPs are closed
immediately with code 4401.

## End-to-end test

1. `docker compose up` → wait until all services are healthy.
2. Open `http://localhost:8080` in two browsers (or two machines with
   different IPs). First visit: claim dialog.
3. Upload an mp3 in window A → appears immediately in window B (`sound_added`).
4. Click the sound in window B → **both** windows play audio; history shows
   the play.
5. Refresh window A → stays signed in (IP match).

## Known limitations

- No sample-accurate sync; clients hear sounds with ~50–200 ms drift.
- Browser autoplay requires a first user gesture (the claim button covers it).
- No per-user quota — suitable for small internal use.
