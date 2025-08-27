FROM python:3.13-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/.venv/bin:/root/.cargo/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=3.13

# install OS-level deps once in base (so we don't repeat in each stage)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------
# Stage: Install Python deps
# -------------------------------
FROM base AS python-deps

ARG INSTALL_DEV_DEPENDENCIES=false

COPY pyproject.toml uv.lock ./

RUN pip install uv==0.8.13 && \
    if [ "$INSTALL_DEV_DEPENDENCIES" = "true" ]; then \
        uv sync --frozen; \
    else \
        uv sync --frozen --no-dev; \
    fi


# -------------------------------
# Stage: Runtime
# -------------------------------
FROM base AS runtime

COPY --from=python-deps ./.venv ./.venv

RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

COPY src/ ./src
COPY config.yaml ./config.yaml

EXPOSE 8083

CMD ["uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8083"]