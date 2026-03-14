FROM python:3.13-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ─── deps ──────────────────────────────────────────────────────────────────────
FROM base AS deps

WORKDIR /app

# Regular COPY (not --link) to avoid opaque whiteout on /bin/ hiding /bin/sh
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /bin/uv
COPY --link pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev --no-install-project

# ─── runtime ───────────────────────────────────────────────────────────────────
FROM base AS runtime

WORKDIR /mlflow

COPY --link --from=deps /app/.venv /app/.venv

RUN mkdir -p /mlflow/artifacts /mlflow/mlruns

EXPOSE 5000

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
