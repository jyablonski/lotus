FROM python:3.13-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/.venv/bin:/root/.cargo/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=3.13

# install OS-level deps once in base
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------
# Stage: Install Python deps
# -------------------------------
FROM base AS python-deps

COPY pyproject.toml uv.lock ./

RUN pip install uv==0.8.13 && \
    uv sync --frozen --no-dev

# -------------------------------
# Stage: Runtime
# -------------------------------
FROM base AS runtime

COPY --from=python-deps ./.venv ./.venv

# Run as root to avoid permission issues with mounted volumes
WORKDIR /mlflow

# Create directories for artifacts and data
RUN mkdir -p /mlflow/artifacts /mlflow/mlruns

EXPOSE 5000

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]