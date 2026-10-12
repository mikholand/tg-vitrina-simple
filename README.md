# tg-vitrina — Telegram Mini App storefront (single-shop)

[![CI](https://github.com/mikholand/tg-vitrina-simple/actions/workflows/ci.yml/badge.svg)](https://github.com/mikholand/tg-vitrina-simple/actions/workflows/ci.yml)

A self-hosted storefront that turns a single Telegram channel into a
browsable, shoppable catalog inside a Telegram Mini App. One deployment
serves exactly one shop/channel — see `docs/architecture.md` for why that
choice simplifies the whole data model.

## Architecture at a glance

```
Telegram channel
      │  new posts                 │ historical backfill
      ▼                             ▼
   bot (aiogram)              userbot (Pyrogram)
      │                             │  POST /api/v1/internal/sync
      └───────────────┬─────────────┘
                       ▼
                  RawPost (Postgres)
                       │
                       ▼
             extractor (OpenRouter LLM)
                       │  drafts
                       ▼
                 Product (status=draft)
                       │  seller reviews/edits in the Mini App
                       ▼
                 Product (status=published)
                       │
                       ▼
            backend API  ──serves──▶  frontend (Vue3 Mini App)
```

See `docs/architecture.md` for the detailed data flow, the resumable sync
cursor mechanics, and the single-shop design rationale.

## Services

| Service    | Image/build          | Role                                                              |
|------------|-----------------------|--------------------------------------------------------------------|
| `database` | `postgres:16-alpine`  | Postgres data store                                               |
| `backend`  | `backend/Dockerfile`  | FastAPI API (granian), runs Alembic migrations on boot            |
| `bot`      | same image as backend | aiogram bot, ingests new channel posts in real time                |
| `extractor`| same image as backend | polls RawPosts, drafts Products via an OpenRouter LLM call         |
| `userbot`  | `userbot/Dockerfile`  | Pyrogram client, resumable historical channel backfill             |
| `frontend` | `frontend/Dockerfile` | Vue3/Vite Mini App, built static bundle served by nginx            |
| `traefik`  | `traefik:v3.1`        | Reverse proxy / router (dev profile only — see below)             |

`backend`, `bot`, and `extractor` all run from the **same built image**
(`backend/Dockerfile`); only the `command:` differs per compose service.

## Prerequisites

- Docker Engine + Docker Compose v2 (`docker compose version`)
- A Telegram bot token (`BOT_TOKEN`) with admin access to the source channel
- Telegram API credentials for the userbot (`USERBOT_API_ID`/`USERBOT_API_HASH`,
  from https://my.telegram.org) and a pre-generated Pyrogram session string
  (`USERBOT_SESSION`) — generate this locally, it is never derived at runtime
- An OpenRouter API key if you want automatic draft extraction (`OPENROUTER_API_KEY`)

## Setup

```bash
cp .env.example .env
# edit .env: fill in STORE_*, TELEGRAM_CHANNEL_ID, BOT_TOKEN, USERBOT_*,
# OPENROUTER_API_KEY, POSTGRES_*, JWT_SECRET, INTERNAL_API_TOKEN, etc.

make up        # builds images, starts the stack + the dev Traefik router
make migrate   # optional: migrations also run automatically on backend boot
make logs      # follow all service logs
```

Once up, the Mini App is reachable through Traefik on `http://localhost/`
(dev profile), with `/api/*` and `/media/*` routed to the backend and
everything else served by the frontend. Point your Telegram bot's Mini App
URL at that host once you have real TLS (see "Dev vs prod" below).

## Dev vs prod

- **Dev**: `make up` starts the `traefik` service (compose `dev` profile)
  using `traefik/traefik.dev.yml` — plain HTTP on port 80, Traefik dashboard
  exposed insecurely on 8080. Fine for localhost/LAN testing, not for the
  public internet.
- **Prod**: swap the mounted static config to `traefik/traefik.prod.yml`,
  which adds an HTTPS `:443` entrypoint, an HTTP→HTTPS redirect, and a
  commented-out Let's Encrypt ACME resolver stub. To go live: point DNS at
  the host, uncomment the `certificatesResolvers` block in that file with a
  real monitored email address, and add `tls.certresolver=letsencrypt` +
  the `websecure` entrypoint to the `backend`/`frontend` Traefik labels in
  `docker-compose.yml`.

## Useful commands

See the `Makefile` for the full list: `up`, `down`, `logs`, `migrate`,
`shell-backend`, `shell-userbot`, `build`, `test`. `make test` runs the
backend's pytest suite locally via `uv` (not in a container) since the
tests use an in-memory SQLite DB and need no other services running.
