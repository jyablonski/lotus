FROM python:3.13-slim AS base

# 1. Add git (required for dbt deps) and clean up
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/app/.venv/bin:/root/.cargo/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=3.13 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Stage: Builder (Install Deps & Project)
# -------------------------------
FROM base AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY services/dagster/pyproject.toml services/dagster/uv.lock ./

RUN uv sync --no-install-project --no-dev

# -------------------------------
# Stage: Runtime
# -------------------------------
FROM base AS runtime

WORKDIR /app

RUN useradd --create-home appuser \
    && mkdir -p /tmp/io_manager_storage/compute_logs \
    && mkdir -p /tmp/io_manager_storage/artifacts \
    && chown -R appuser:appuser /tmp/io_manager_storage

USER appuser

# Copy the environment from builder
COPY --from=builder /app/.venv /app/.venv

# --- HANDLE DBT FOLDER ---
# Your python code looks for dbt at "../../../../dbt" relative to src/dagster_project/dbt_config.py
# If dbt_config.py is at: /app/src/dagster_project/dbt_config.py
# Up 4 levels is: /app/
# So we need to copy your dbt folder to /app/dbt
# NOTE: Build context is project root, so we copy services/dbt
COPY --chown=appuser:appuser services/dbt /app/dbt

# --- HANDLE FEAST REPO FOLDER ---
# Copy the Feast repository to /app/feast_repo
# NOTE: Build context is project root, so we copy services/dagster/feast_repo
COPY --chown=appuser:appuser services/dagster/feast_repo /app/feast_repo

# Set Environment Variables
# 1. Point dbt to the correct profile dir inside the container
ENV DBT_PROFILES_DIR="/app/dbt"
# 2. Tell Dagster where the code is (optional but good practice)
ENV DAGSTER_CURRENT_IMAGE="dagster_server_image"
# 3. Add src to Python path so dagster_project can be imported
ENV PYTHONPATH="/app/src:$PYTHONPATH"
# NOTE: No DAGSTER_HOME needed - run containers get instance config serialized from daemon

# Copy source code at the end
COPY --chown=appuser:appuser services/dagster/src /app/src

EXPOSE 4000

# The standard Dagster Code Server command
# -h 0.0.0.0: Listen on all interfaces (required for Docker)
# -p 4000: The port we exposed
# -m dagster_project.definitions: The python module to load
CMD ["dagster", "code-server", "start", "-h", "0.0.0.0", "-p", "4000", "-m", "dagster_project.definitions"]
