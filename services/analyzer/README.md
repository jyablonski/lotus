# Analyzer

Analyzer is a REST API Service written in Python w/ FastAPI. It's primarily used to run ML Models from within the `services/experiments` directory to extract things like topics and sentiment from user journals

## ML Model Setup

### Overview

The analyzer service integrates with MLflow to load and serve ML models for sentiment analysis and topic extraction. Models are loaded once at application startup and reused across all requests for optimal performance.

### Architecture

#### Model Clients

The service uses a base class architecture for MLflow model clients:

- **`BaseMLflowClient`** (`src/clients/base_mlflow_client.py`)
  - Base class that handles common MLflow operations
  - Manages model loading, version resolution, metadata tracking
  - Provides `load_model()`, `is_ready()`, and `get_model_info()` methods
  - Eliminates code duplication between ML clients

The service uses three main client classes for ML operations:

1. **`SentimentClient`** (`src/clients/ml_sentiment_client.py`)
   - Inherits from `BaseMLflowClient`
   - Model: `journal_sentiment_analyzer`
   - Purpose: Analyzes sentiment (positive/negative/neutral) from journal text
   - Features: Confidence scoring, batch processing, trend analysis

2. **`TopicClient`** (`src/clients/ml_topic_client.py`)
   - Inherits from `BaseMLflowClient`
   - Model: `adaptive_journal_topics`
   - Purpose: Extracts topics from journal entries
   - Features: Adaptive topic extraction based on text length

3. **`OpenAITopicClient`** (`src/clients/openai_topic_client.py`)
   - Uses OpenAI API via instructor library
   - Purpose: Alternative topic extraction using LLMs
   - Tracks experiments in MLflow

#### Singleton Pattern

All ML clients use a singleton pattern via `@lru_cache` in `src/dependencies.py`:

- Models are loaded once at startup in the `lifespan` function
- All subsequent requests reuse the same client instance
- This ensures 1000 requests = 1 model load (not 1000 model loads)

#### Model Loading

Models are loaded during application startup in `src/main.py`:

- Both `TopicClient` and `SentimentClient` models are loaded synchronously
- If model loading fails, the application will not start (configurable)
- Models are loaded from MLflow Model Registry using the `models:/` URI format
- Default version is `"latest"`, but specific versions can be specified

### Configuration

MLflow configuration is managed through `src/config.py`:

```python
mlflow_tracking_uri: str = os.getenv("MLFLOW_CONN_URI", "http://localhost:5000")
```

**Environment Variables:**

- `MLFLOW_CONN_URI`: MLflow tracking server URI (default: `http://localhost:5000`)
- `OPENAI_API_KEY`: Required for OpenAI topic client

### Model Registry

Models are loaded from MLflow Model Registry using the format:

- `models:/{model_name}/{version}`
- Example: `models:/journal_sentiment_analyzer/latest`

The clients automatically:

- Resolve "latest" to the actual version number
- Capture model version and run ID metadata
- Log model loading status and version information

### Model Storage Requirements

Models **must** be logged to MLflow in a specific format for the analyzer service to use them:

#### Required Format

1. **PyFunc Model Wrapper**: Models must be logged as `mlflow.pyfunc.PythonModel` instances
   - The wrapper class must extend `mlflow.pyfunc.PythonModel`
   - Must implement `load_context()` to load artifacts
   - Must implement `predict()` that accepts a pandas DataFrame
   - **The wrapper handles all preprocessing internally** - no preprocessing needed in API code

   **Preprocessing Included in Wrapper:**
   - **Sentiment Models**: Text normalization (lowercasing, whitespace cleanup, stripping)
   - **Topic Models**: Adaptive topic extraction based on text length:
     - Short entries (< 20 words): min_confidence=0.25, max_topics=2
     - Medium entries (20-50 words): min_confidence=0.20, max_topics=4
     - Long entries (> 50 words): min_confidence=0.15, max_topics=6
   - All text preprocessing (TF-IDF vectorization, feature extraction) is handled by the sklearn pipeline within the wrapper
   - The API simply passes raw text and receives formatted results - no preprocessing duplication needed

2. **Artifacts**: Models must include required artifacts in the `artifacts` dictionary:

   **Sentiment Model Artifacts:**
   - `sklearn_pipeline`: Path to saved sklearn pipeline (via `mlflow.sklearn.save_model()`)
   - `label_encoder`: Path to pickled label encoder
   - `sentiment_labels`: Path to sentiment labels mapping (parquet file)

   **Topic Model Artifacts:**
   - `sklearn_pipeline`: Path to saved sklearn pipeline (via `mlflow.sklearn.save_model()`)
   - `topic_labels`: Path to pickled topic labels dictionary
   - `model_config`: Path to pickled model configuration dictionary

3. **Logging Example**:

   ```python
   mlflow.pyfunc.log_model(
       artifact_path="sentiment_model",
       python_model=SentimentAnalyzerWrapper(),  # Your wrapper class
       artifacts={
           "sklearn_pipeline": sklearn_path,
           "label_encoder": label_encoder_path,
           "sentiment_labels": sentiment_labels_path,
       },
       code_paths=[__file__],  # Include wrapper code
       pip_requirements=["pandas", "numpy", "scikit-learn", "mlflow"],
       registered_model_name="journal_sentiment_analyzer",  # Exact name required
   )
   ```

#### Training Scripts

Reference implementations can be found in:

- `services/experiments/src/training/train_sentiment_analysis.py`
- `services/experiments/src/training/train_topics.py`

These scripts demonstrate the complete workflow for:

- Creating the pyfunc wrapper class
- Training the underlying sklearn pipeline
- Saving artifacts
- Logging to MLflow with proper format
- Registering models with correct names

### Health Endpoints

Health check endpoints are available for monitoring model status:

- `/v1/health/sentiment` - Checks sentiment model status
- `/v1/health/topics` - Checks ML topic model status
- `/v1/health/openai/topics` - Checks OpenAI topic service status

All health endpoints return:

- `status`: "healthy" or "unhealthy"
- `service`: Service identifier
- Model metadata (version, run_id, etc.) when healthy

### Error Handling

- Model loading failures during startup will prevent the application from starting (by default)
- Individual prediction failures are caught and logged at the endpoint level
- Health endpoints return 503 status when models are not ready
- All clients have `is_ready()` methods to check model status before use

### Usage Example

The wrapper classes handle all preprocessing internally, so the API code is simple:

```python
from src.dependencies import get_sentiment_client

@router.post("/analyze")
def analyze(
    sentiment_client: SentimentClient = Depends(get_sentiment_client)
):
    # No preprocessing needed - just pass raw text!
    result = sentiment_client.predict_sentiment(text)
    return result
```

**Key Points:**

- Raw text is passed directly to the client methods
- All text preprocessing (normalization, vectorization, etc.) happens inside the MLflow pyfunc wrapper
- The wrapper returns fully formatted results with sentiment/topics, confidence scores, and metadata
- No need to duplicate preprocessing logic in the API code

## Notes

Testing got a little scuffed, having to spin up MLFlow every time would have been a pain and I don't have 24/7 remote instances running to leverage here either
