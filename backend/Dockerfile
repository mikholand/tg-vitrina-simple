# syntax=docker/dockerfile:1
#
# Single image reused for all three backend processes that share this
# codebase: the API server (granian), the Telegram bot (aiogram), and the
# extractor worker. Which process runs is selected by the compose service's
# `command:` — see docker-compose.yml.

FROM python:3.12-slim AS builder

# Install uv (pinned, copied straight from its official distroless image).
COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Install dependencies first (cache-friendly: only re-runs when
# pyproject.toml/uv.lock change, not on every source edit).
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Now copy the actual application source and install the project itself.
COPY app ./app
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.12-slim AS runtime

RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /media && chown -R app:app /app /media

USER app

EXPOSE 8000

# Default process is the API server (app/__main__.py wraps granian and
# reads BACKEND_HOST/BACKEND_PORT/BACKEND_WORKERS). The `bot` and
# `extractor` compose services override this with
# `command: python -m app.telegram` / `command: python -m app.extractor`.
CMD ["python", "-m", "app"]
