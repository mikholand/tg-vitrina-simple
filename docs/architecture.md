# Architecture

## Data flow

```
                         ┌─────────────────────────┐
                         │   Telegram channel       │
                         │ (TELEGRAM_CHANNEL_ID)    │
                         └──────┬─────────────┬─────┘
                new posts       │             │  one-time/periodic
                (live)          ▼             ▼  historical backfill
                     ┌────────────────┐  ┌──────────────────┐
                     │  bot (aiogram) │  │ userbot (Pyrogram)│
                     │  app/telegram  │  │  userbot/app      │
                     └───────┬────────┘  └─────────┬─────────┘
                              │ writes directly      │ HTTP POST
                              │ via shared DI/DB      │ /api/v1/internal/sync/*
                              ▼                       ▼ (X-Internal-Token)
                     ┌─────────────────────────────────────┐
                     │          Postgres: raw_post          │
                     │  (deduped by channel_id+message_id  │
                     │   or media_group_id)                 │
                     └───────────────────┬───────────────────┘
                                          │ polled every
                                          │ EXTRACTOR_POLL_INTERVAL
                                          ▼
                     ┌─────────────────────────────────────┐
                     │   extractor (app/extractor)           │
                     │   OpenRouter LLM call → structured    │
                     │   title/price/description/category    │
                     └───────────────────┬───────────────────┘
                                          │ creates
                                          ▼
                     ┌─────────────────────────────────────┐
                     │  Postgres: product (status=draft)     │
                     └───────────────────┬───────────────────┘
                                          │ seller reviews/edits
                                          │ in the Mini App (seller UI)
                                          ▼
                     ┌─────────────────────────────────────┐
                     │  Postgres: product (status=published) │
                     └───────────────────┬───────────────────┘
                                          │ served by
                                          ▼
                     ┌─────────────────────────────────────┐
                     │   backend API (FastAPI, granian)      │
                     │   /api/v1/catalog, /favorites, ...    │
                     └───────────────────┬───────────────────┘
                                          │ same-origin reverse proxy
                                          ▼
                     ┌─────────────────────────────────────┐
                     │  frontend: Vue3/Vite Mini App          │
                     │  (served as a static bundle by nginx)  │
                     └─────────────────────────────────────┘
```

Media (photos) flow separately: both the `bot` and the `userbot` download
photos straight to the shared `media/` volume (`MEDIA_ROOT/raw_posts/
{channel_id}/{message_id}/{index}.jpg`, see `backend/app/telegram/
handlers.py` and `userbot/app/sync_runner.py`). The backend serves that same
directory tree back out at `/media` via a FastAPI `StaticFiles` mount
(`backend/app/asgi/app.py`), and the frontend's nginx reverse-proxies
`/media/*` to the backend so it resolves same-origin in the browser.

## Resumable sync mechanics (cursor / stop_id)

Historical backfill is driven by a single singleton row,
`sync_state` (id=1, see `backend/app/entities/sync_state.py`) — there is
one sync checkpoint for the one channel this deployment serves.

- **`stop_id`**: the upper boundary for the *current* backfill pass — the
  newest `message_id` the backend already knew about when the pass started
  (`SyncOrchestrationService.claim_job`, `backend/app/services/sync.py`).
  It is fixed once per pass and never changes mid-pass, even across
  retries/resumes, so a pass always walks a stable, closed range instead of
  chasing a moving target while new posts keep arriving via the live `bot`.
- **`cursor`**: the oldest `message_id` successfully ingested *so far* in
  the current/last pass. It only advances after a batch has been durably
  persisted (ingested + progress POSTed), never speculatively.
- **Fresh start**: `cursor` is `None`, so the userbot's `SyncRunner` begins
  walking backwards from `stop_id` (`offset_id = job.stop_id`).
- **Resume** (after an interruption, crash, or explicit stop/retry):
  `cursor` is not `None`, so the next pass resumes from exactly where it
  left off (`offset_id = job.cursor`), re-using the *same* `stop_id` fixed
  at the start of the original pass.
- Each batch fetched via Pyrogram is deduplicated server-side on ingest
  (`channel_id` + `message_id`, or `media_group_id` for multi-photo posts),
  so a resumed pass re-ingesting a slightly overlapping batch is harmless.
- `SyncStatus` transitions: `IDLE` → `REQUESTED` (seller/admin asks for a
  backfill) → `RUNNING` (userbot claims the job via `GET .../internal/
  sync/job`) → `DONE` on natural exhaustion of Pyrogram's history
  generator, or `FAILED`/`INTERRUPTED` otherwise. A `FAILED` pass schedules
  a `retry_at` (default 10 minutes, or `retry_after_seconds` from the
  userbot on a caught exception) rather than retrying immediately. The
  userbot also cooperatively checks `GET .../internal/sync/stop-requested`
  between batches so an admin can cancel a long-running pass.

## Single-shop design

This deployment is intentionally **single-shop**: the store's identity
(`STORE_NAME`, `STORE_DESCRIPTION`, `STORE_LOGO`, `STORE_CONTACT_TG`) and
its one source channel (`TELEGRAM_CHANNEL_ID`) are **environment
configuration**, not rows in a database. There is exactly one `sync_state`
singleton, one Postgres database, one bot token, one userbot session.

Contrast with a multi-tenant design: a `shops` table, `shop_id` foreign
keys on every domain entity (`product`, `raw_post`, `sync_state`,
`category`, ...), and tenant-resolution middleware (from a subdomain, a
header, or a path segment) that scopes every query. None of that exists
here. This directly simplifies the schema and the codebase:

- No `shop_id` column/FK/index on `raw_post`, `product`, `category`,
  `sync_state`, `favorite`, or `view` — one fewer join/filter on every
  query, one fewer migration concern when adding new tables.
- No tenant-resolution middleware or per-request "which shop is this"
  context plumbing through the DI container.
- `sync_state` can be a true singleton row (`id=1`) instead of one row per
  shop.
- Horizontal "add another shop" scaling is explicitly out of scope: running
  a second shop means standing up a second full deployment (its own
  `.env`, its own Postgres, its own compose project) rather than adding a
  row to a `shops` table. That is a deliberate complexity/flexibility
  trade-off for a project with a known, fixed scope of "one Telegram
  channel, one storefront."

## Deployment topology

See `docker-compose.yml` for the full service graph and
`traefik/traefik.dev.yml` / `traefik/traefik.prod.yml` for the two router
configurations. In short: `backend`, `bot`, and `extractor` are the same
built image (`backend/Dockerfile`) running three different
`command:`s against one Postgres instance; `userbot` is a separate image
(needs a C toolchain to build the `tgcrypto` extension); `frontend` is a
static Vue bundle served by nginx, which also reverse-proxies `/api/*` and
`/media/*` to `backend` so the SPA's same-origin `axios` client
(`baseURL: '/api/v1'`) works without CORS in both dev and prod.
