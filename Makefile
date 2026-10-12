.PHONY: up down logs migrate shell-backend shell-userbot build test

COMPOSE := docker compose

# Bring the whole stack up, including the dev-profile Traefik router.
# Swap to `docker compose up -d` (no --profile) if you're fronting the
# stack with something else, or to traefik.prod.yml for a real deployment
# (see traefik/traefik.prod.yml and docs/architecture.md).
up:
	$(COMPOSE) --profile dev up -d --build

down:
	$(COMPOSE) --profile dev down

logs:
	$(COMPOSE) --profile dev logs -f

# Run pending Alembic migrations inside a one-off backend container. Useful
# standalone, e.g. after pulling new migrations without restarting
# everything (the `backend` service also runs this automatically on boot).
migrate:
	$(COMPOSE) run --rm backend alembic upgrade head

shell-backend:
	$(COMPOSE) run --rm backend bash

shell-userbot:
	$(COMPOSE) run --rm userbot bash

build:
	$(COMPOSE) build

# Runs the backend test suite via uv, directly on the host — NOT inside a
# container. Rationale: the backend's tests use aiosqlite (see
# backend/pyproject.toml dev deps) instead of a live Postgres, so they need
# no services running and a transient container would only add overhead.
# Requires `uv` installed locally; `cd backend && uv sync` once beforehand.
test:
	cd backend && uv run pytest
