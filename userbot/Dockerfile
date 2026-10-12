# syntax=docker/dockerfile:1
#
# Standalone Pyrogram userbot used for one-time/periodic history backfill.
# Needs a C toolchain to build the `tgcrypto` extension (no manylinux wheel
# is guaranteed for every platform this may run on), so the build stage
# pulls in build-essential.

FROM python:3.12-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# NOTE: this package has no uv.lock checked in (unlike backend/), so we
# resolve on the fly rather than using --frozen. Generate and commit a
# uv.lock here if reproducible builds become a requirement.
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

COPY app ./app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev


FROM python:3.12-slim AS runtime

# tgcrypto is a compiled extension, but it links against glibc only (no
# extra runtime shared libs needed beyond what python:3.12-slim ships).
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /media && chown -R app:app /app /media

USER app

CMD ["python", "-m", "app"]
