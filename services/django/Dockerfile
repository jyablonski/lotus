FROM python:3.13-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

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

# ─── runtime ───────────────────────────────────────────────────────────────────
FROM base AS runtime

WORKDIR /app

RUN useradd --create-home appuser

COPY --link --from=deps /app/.venv /app/.venv

USER appuser

COPY --link manage.py ./
COPY --link lotus_admin/ ./lotus_admin/
COPY --link core/ ./core/
COPY --link entrypoint.sh ./

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
