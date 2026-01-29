# Analyzer Service - Agent Guide

FastAPI service for ML/LLM-powered sentiment analysis and topic extraction from journal entries.

## Technology Stack

- **Framework**: FastAPI
- **Language**: Python 3.13
- **Database**: PostgreSQL (via SQLAlchemy)
- **ML Framework**: MLflow for model registry
- **LLM**: OpenAI API (via instructor library)
- **Dependency Management**: uv (pyproject.toml)

## Architecture Patterns

### ML Client Architecture

The service uses a **base class pattern** for MLflow model clients:

1. **`BaseMLflowClient`** (`src/clients/base_mlflow_client.py`)
   - Handles common MLflow operations
   - Manages model loading, version resolution, metadata tracking
   - Provides `load_model()`, `is_ready()`, and `get_model_info()` methods

2. **Concrete Clients**:
   - `SentimentClient` - Sentiment analysis (inherits from `BaseMLflowClient`)
   - `TopicClient` - Topic extraction (inherits from `BaseMLflowClient`)
   - `OpenAITopicClient` - LLM-based topic extraction (uses OpenAI API)

### Singleton Pattern

All ML clients use **singleton pattern** via `@lru_cache` in `src/dependencies.py`:

- Models are loaded **once** at application startup in the `lifespan` function
- All subsequent requests reuse the same client instance
- This ensures optimal performance (1000 requests = 1 model load, not 1000)

### Model Loading

Models are loaded synchronously during application startup:

- Both `TopicClient` and `SentimentClient` models are loaded in `src/main.py` lifespan
- If model loading fails, the application will **not start** (configurable)
- Models are loaded from MLflow Model Registry using `models:/{model_name}/{version}` format
- Default version is `"latest"`, but specific versions can be specified

## Code Organization

```
src/
├── main.py                 # FastAPI app and lifespan (model loading)
├── config.py              # Configuration (Pydantic Settings)
├── database.py            # SQLAlchemy database connection
├── logger.py              # Logging setup
├── dependencies.py        # FastAPI dependencies (singleton clients)
├── clients/               # ML model clients
│   ├── base_mlflow_client.py
│   ├── ml_sentiment_client.py
│   ├── ml_topic_client.py
│   └── openai_topic_client.py
├── routers/               # API route handlers
│   └── v1/
│       ├── __init__.py
│       ├── journal_sentiments.py
│       ├── journal_topics.py
│       └── journal_topics_openai.py
├── crud/                  # Database CRUD operations
├── models/                # SQLAlchemy models
└── schemas/               # Pydantic schemas
```

## Key Patterns

### Router Organization

- Routes are organized under `/v1` prefix
- Each domain (sentiments, topics) has its own router file
- Routers are included in `src/main.py` via `app.include_router(v1_router, prefix="/v1")`

### Dependency Injection

- Use FastAPI's dependency injection for ML clients
- Clients are accessed via `get_sentiment_client()` and `get_topic_client()` functions
- These functions use `@lru_cache` to ensure singleton instances

### Error Handling

- Use `HTTPException` for API errors
- Log errors with context before raising exceptions
- Return appropriate HTTP status codes (400, 404, 500, etc.)

### Database Access

- Use SQLAlchemy for database operations
- CRUD operations are in `src/crud/` directory
- Models are defined in `src/models/`

## Testing

### Test Structure

- Tests are in `tests/` directory
- Use `pytest` with `pytest-cov` for coverage
- Test fixtures in `tests/conftest.py`
- Integration tests in `tests/integration/`

### Test Markers

- `@pytest.mark.wip` - Work in progress
- `@pytest.mark.infrastructure` - Tests requiring infrastructure (DB, HTTP endpoints)

### Running Tests

```bash
# From service directory
pytest

# With coverage
pytest --cov=src --cov-report=term-missing
```

## Configuration

### Environment Variables

- `MLFLOW_CONN_URI` - MLflow tracking server URI (default: `http://localhost:5000`)
- `OPENAI_API_KEY` - Required for OpenAI topic client
- `ENV_TYPE` - Environment type (`docker_dev`, `local`, etc.)
- `ENABLE_V1_ROUTER` - Enable v1 router (default: `true`)

### Configuration File

- `config.yaml` - Service configuration (mounted as volume in Docker)
- Configuration is loaded via `src/config.py` using Pydantic Settings

## Model Registry

### Model Format Requirements

Models **must** be logged to MLflow as `mlflow.pyfunc.PythonModel` instances:

- The wrapper class must extend `mlflow.pyfunc.PythonModel`
- Models are loaded using `mlflow.pyfunc.load_model()` with `models:/` URI format

### Model Names

- `journal_sentiment_analyzer` - Sentiment analysis model
- `adaptive_journal_topics` - Topic extraction model

### Model Versioning

- Use `"latest"` for production (resolves to most recent version)
- Specify version numbers for testing specific versions
- Model version metadata is tracked and logged

## Key Files to Understand

Before making changes:

1. **`src/main.py`** - Application entry point, lifespan, model loading
2. **`src/dependencies.py`** - FastAPI dependencies and singleton clients
3. **`src/clients/base_mlflow_client.py`** - Base class for ML clients
4. **`src/config.py`** - Configuration management
5. **`src/routers/v1/`** - API route handlers
6. **`tests/conftest.py`** - Test fixtures and setup

## Common Tasks

### Adding a New ML Model Client

1. Create a new client class inheriting from `BaseMLflowClient`
2. Implement model-specific prediction methods
3. Add dependency function in `src/dependencies.py` with `@lru_cache`
4. Load model in `src/main.py` lifespan function
5. Create router endpoints in `src/routers/v1/`

### Adding a New API Endpoint

1. Add route handler in appropriate router file (`src/routers/v1/`)
2. Use dependency injection for ML clients
3. Add Pydantic schemas in `src/schemas/` if needed
4. Add CRUD operations in `src/crud/` if database access is needed
5. Write tests in `tests/integration/`

### Debugging Model Loading Issues

1. Check MLflow connection: `MLFLOW_CONN_URI` environment variable
2. Verify model exists in MLflow registry: `models:/{model_name}/latest`
3. Check logs during startup for model loading errors
4. Ensure model is logged as `mlflow.pyfunc.PythonModel`

## Code Style

- Follow root `pyproject.toml` Ruff configuration
- Use type hints for all function signatures
- Use Pydantic models for request/response validation
- Use structured logging (via `src/logger.py`)
- Keep functions focused and single-purpose
