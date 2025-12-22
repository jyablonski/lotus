FROM python:3.13-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/.venv/bin:/root/.cargo/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=3.13

# install OS-level deps once in base (so we don't repeat in each stage)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Stage: Install Python deps
# -------------------------------
FROM base AS python-deps

ARG INSTALL_DEV_DEPENDENCIES=false

COPY pyproject.toml uv.lock ./

RUN pip install uv==0.9.18 && \
    if [ "$INSTALL_DEV_DEPENDENCIES" = "true" ]; then \
    uv sync --frozen --no-install-project; \
    else \
    uv sync --frozen --no-dev --no-install-project; \
    fi


# -------------------------------
# Stage: Runtime
# -------------------------------
FROM base AS runtime

COPY --from=python-deps ./.venv ./.venv

RUN useradd --create-home appuser
WORKDIR /app
USER appuser

COPY manage.py ./
COPY lotus_admin/ ./lotus_admin/
COPY core/ ./core/
COPY entrypoint.sh ./

USER root
USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
