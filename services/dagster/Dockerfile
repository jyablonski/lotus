FROM python:3.13-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    DAGSTER_HOME=/opt/dagster/dagster_home

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ─── deps ──────────────────────────────────────────────────────────────────────
FROM base AS deps

WORKDIR /app

# Regular COPY (not --link) to avoid opaque whiteout on /bin/ hiding /bin/sh
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /bin/uv
COPY --link services/dagster/pyproject.toml services/dagster/uv.lock ./

RUN uv sync --locked --no-install-project --no-dev

# ─── runtime ───────────────────────────────────────────────────────────────────
FROM base AS runtime

WORKDIR /app

RUN useradd --create-home appuser \
    && mkdir -p /tmp/io_manager_storage/compute_logs \
    && mkdir -p /tmp/io_manager_storage/artifacts \
    && mkdir -p $DAGSTER_HOME \
    && chown -R appuser:appuser /tmp/io_manager_storage \
    && chown -R appuser:appuser $DAGSTER_HOME

USER appuser

COPY --link --from=deps /app/.venv /app/.venv

# Regular COPY for --chown: COPY --link with named users fails because the
# independent snapshot can't resolve usernames added by RUN in the same stage.
# Your python code looks for dbt at "../../../../dbt" relative to src/dagster_project/dbt_config.py
# NOTE: Build context is project root, so we copy services/dbt
COPY --chown=appuser:appuser services/dbt /app/dbt

COPY --chown=appuser:appuser services/dagster/feast_repo /app/feast_repo

# Copy dagster.yaml and workspace.yaml to DAGSTER_HOME for webserver/daemon
COPY --chown=appuser:appuser services/dagster/dagster.yaml services/dagster/workspace.yaml $DAGSTER_HOME/

# Copy source code last so changes here don't bust earlier cache layers
COPY --chown=appuser:appuser services/dagster/src /app/src

ENV DBT_PROFILES_DIR="/app/dbt/profiles"
ENV DAGSTER_CURRENT_IMAGE="dagster_server_image"
ENV PYTHONPATH="/app/src"

EXPOSE 4000 3000

CMD ["dagster", "code-server", "start", "-h", "0.0.0.0", "-p", "4000", "-m", "dagster_project.definitions"]
