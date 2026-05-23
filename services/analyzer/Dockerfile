FROM python:3.13-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    HF_HOME=/app/.cache/huggingface \
    PATH="/app/.venv/bin:$PATH" \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ─── deps ──────────────────────────────────────────────────────────────────────
FROM base AS deps

ARG INSTALL_DEV_DEPENDENCIES=false

WORKDIR /app

# Regular COPY (not --link) to avoid opaque whiteout on /bin/ hiding /bin/sh
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /bin/uv
COPY --link pyproject.toml uv.lock ./

RUN if [ "$INSTALL_DEV_DEPENDENCIES" = "true" ]; then \
        uv sync --locked --no-install-project; \
    else \
        uv sync --locked --no-dev --no-install-project; \
    fi

RUN /app/.venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ─── runtime ───────────────────────────────────────────────────────────────────
FROM base AS runtime

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

WORKDIR /app

RUN groupadd --gid 10001 appuser && \
    useradd --uid 10001 --gid 10001 --create-home appuser

COPY --from=deps /app/.venv /app/.venv
COPY --chown=10001:10001 --from=deps /app/.cache /app/.cache

USER appuser

COPY --link src/ ./src
COPY --link config.yaml ./

EXPOSE 8083

CMD ["uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8083"]
