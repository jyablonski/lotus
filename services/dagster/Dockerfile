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

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

COPY src/ ./src

# Sync again - this installs 'dagster_project' into the .venv
RUN uv sync --frozen --no-dev

# -------------------------------
# Stage: Runtime
# -------------------------------
FROM base AS runtime

WORKDIR /app

RUN useradd --create-home appuser
USER appuser

# Copy the environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# --- HANDLE DBT FOLDER ---
# Your python code looks for dbt at "../../../../dbt" relative to src/dagster_project/defs/project.py
# If project.py is at: /app/src/dagster_project/defs/project.py
# Up 4 levels is: /app/
# So we need to copy your dbt folder to /app/dbt
# NOTE: This requires your build context to include the dbt folder (see instructions below)
COPY --chown=appuser:appuser dbt /app/dbt
COPY --chown=appuser:appuser services/dbt/profiles.yml /app/dbt/profiles.yml

# Set Environment Variables
# 1. Point dbt to the correct profile dir inside the container
ENV DBT_PROFILES_DIR="/app/dbt"
# 2. Tell Dagster where the code is (optional but good practice)
ENV DAGSTER_CURRENT_IMAGE="dagster_project_image"

EXPOSE 4000

# The standard Dagster Code Server command
# -h 0.0.0.0: Listen on all interfaces (required for Docker)
# -p 4000: The port we exposed
# -m dagster_project.definitions: The python module to load
CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-m", "dagster_project.definitions"]
