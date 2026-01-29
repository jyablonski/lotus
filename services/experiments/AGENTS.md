# Experiments Service - Agent Guide

ML model training service for sentiment analysis and topic extraction. Models are trained here and logged to MLflow for use by the Analyzer service.

## Technology Stack

- **Language**: Python 3.13
- **ML Framework**: scikit-learn, pandas
- **Model Registry**: MLflow 3.3.1+
- **Database**: PostgreSQL (for MLflow backend)
- **Dependency Management**: uv (pyproject.toml)

## Architecture Patterns

### Model Training Workflow

1. **Train Model** - Train ML model using training scripts
2. **Log to MLflow** - Log model, metrics, and artifacts to MLflow
3. **Register Model** - Register model in MLflow Model Registry
4. **Deploy** - Analyzer service loads model from registry

### Model Types

The service trains two main model types:

1. **Sentiment Analyzer** (`src/models/sentiment_analyzer.py`)
   - Model name: `journal_sentiment_analyzer`
   - Purpose: Classify journal sentiment (positive/negative/neutral)
   - Framework: scikit-learn (RoBERTa-based)

2. **Topic Extractor** (`src/models/topic_extractor.py`)
   - Model name: `adaptive_journal_topics`
   - Purpose: Extract topics from journal entries
   - Framework: scikit-learn

### MLflow Integration

- Models are logged as `mlflow.pyfunc.PythonModel` instances
- This allows the Analyzer service to load models consistently
- Model metadata (version, run ID) is tracked
- Models are versioned in MLflow Model Registry

## Code Organization

```
src/
├── models/                   # ML model implementations
│   ├── sentiment_analyzer.py # Sentiment analysis model
│   └── topic_extractor.py    # Topic extraction model
└── training/                 # Training scripts
    ├── train_sentiment_analysis_roberta.py
    ├── train_sentiment_analysis.py
    ├── train_topics.py
    └── train_example.py

tests/
└── models/                   # Model tests
    ├── test_sentiment_analyzer.py
    └── test_topic_extractor.py
```

## Key Patterns

### Model Definition

Models must extend `mlflow.pyfunc.PythonModel`:

```python
import mlflow.pyfunc

class SentimentModel(mlflow.pyfunc.PythonModel):
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def predict(self, context, model_input):
        # Preprocessing
        # Model prediction
        # Postprocessing
        return predictions
```

### Training Script Pattern

```python
import mlflow

# Start MLflow run
with mlflow.start_run():
    # Train model
    model = train_model(data)

    # Log metrics
    mlflow.log_metric("accuracy", accuracy)

    # Log model
    mlflow.pyfunc.log_model(
        artifact_path="model",
        python_model=SentimentModel(model, tokenizer),
        registered_model_name="journal_sentiment_analyzer"
    )
```

### Model Logging

- Use `mlflow.pyfunc.log_model()` for model logging
- Specify `registered_model_name` to register in Model Registry
- Log metrics, parameters, and artifacts
- Use consistent model names (matching Analyzer service expectations)

## Testing

### Test Structure

- Tests are in `tests/models/`
- Use `pytest` with model-specific fixtures
- Test files: `test_*.py`

### Test Markers

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests with MLflow
- `@pytest.mark.slow` - Tests taking > 1 second
- `@pytest.mark.performance` - Performance regression tests

### Running Tests

```bash
# From service directory
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Run specific test
pytest tests/models/test_sentiment_analyzer.py
```

### Test Fixtures

- Model fixtures in `tests/conftest.py`
- Mock MLflow for unit tests
- Use real MLflow for integration tests

## Configuration

### Environment Variables

- `MLFLOW_BACKEND_STORE_URI` - MLflow backend store (PostgreSQL)
- `MLFLOW_ARTIFACTS_DESTINATION` - Artifact storage path
- `MLFLOW_TRACKING_URI` - MLflow tracking server URI

### MLflow Configuration

- Backend store: PostgreSQL (shared with application)
- Artifacts: Local filesystem or S3 (configured in MLflow server)
- Model registry: Managed by MLflow

## Key Files to Understand

Before making changes:

1. **`src/models/sentiment_analyzer.py`** - Sentiment model implementation
2. **`src/models/topic_extractor.py`** - Topic model implementation
3. **`src/training/train_sentiment_analysis_roberta.py`** - Example training script
4. **`tests/models/test_sentiment_analyzer.py`** - Model tests

## Common Tasks

### Training a New Model

1. Create training script in `src/training/`
2. Load and preprocess training data
3. Train model using scikit-learn or other framework
4. Wrap model in `mlflow.pyfunc.PythonModel`
5. Log model to MLflow with `registered_model_name`
6. Verify model appears in MLflow UI
7. Test model loading in Analyzer service

### Updating an Existing Model

1. Modify training script
2. Train new version
3. Log to MLflow (creates new version)
4. Test new version in Analyzer service
5. Promote to production if metrics improve

### Creating a New Model Type

1. Define model class in `src/models/`
2. Extend `mlflow.pyfunc.PythonModel`
3. Implement `predict()` method
4. Create training script
5. Write tests
6. Update Analyzer service to use new model

### Model Versioning

- MLflow automatically versions models
- Use `models:/{model_name}/latest` for latest version
- Use `models:/{model_name}/{version}` for specific version
- Promote models to "Production" stage in MLflow UI

## Code Style

- Follow root `pyproject.toml` Ruff configuration
- Use type hints for all functions
- Document model architecture and hyperparameters
- Use meaningful variable names
- Keep training scripts focused and reproducible

## Model Requirements

### For Analyzer Service Compatibility

Models **must** be logged as `mlflow.pyfunc.PythonModel`:

1. **Wrapper Class**: Extend `mlflow.pyfunc.PythonModel`
2. **Predict Method**: Implement `predict(context, model_input)` method
3. **Input Format**: Accept pandas DataFrame input
4. **Output Format**: Return list of dictionaries or DataFrame
5. **Preprocessing**: Handle all preprocessing in `predict()` method
6. **Postprocessing**: Format predictions consistently

### Model Input/Output

- **Input**: pandas DataFrame with `text` column
- **Output**: List of dictionaries or DataFrame with predictions
- **Sentiment**: `{"sentiment": "positive", "confidence": 0.95, ...}`
- **Topics**: `{"topics": ["topic1", "topic2"], ...}`

## Integration with Analyzer Service

### Model Loading

- Analyzer service loads models using `mlflow.pyfunc.load_model()`
- Uses `models:/{model_name}/latest` URI format
- Models are loaded once at startup (singleton pattern)

### Model Updates

1. Train new model version in Experiments service
2. Log to MLflow (creates new version)
3. Analyzer service loads `latest` version on restart
4. Or specify version explicitly for testing

### Model Testing

- Test model loading in Analyzer service after training
- Verify predictions match expected format
- Check model performance metrics
- Monitor model drift over time

## Best Practices

1. **Reproducibility**: Use fixed random seeds
2. **Versioning**: Always log models with version tracking
3. **Documentation**: Document model architecture and hyperparameters
4. **Testing**: Test models before registering
5. **Metrics**: Log comprehensive metrics (accuracy, precision, recall, etc.)
6. **Artifacts**: Log training data samples and visualizations
7. **Experiments**: Use MLflow experiments to organize runs
8. **Comparison**: Compare model versions in MLflow UI

## Pre-commit Hooks

- Ruff linting and formatting (inherited from root)
- No model-specific hooks

## Deployment

- This service is **not deployed** as a running service
- Training scripts are run manually or via scheduled jobs
- Models are stored in MLflow Model Registry
- Analyzer service loads models from registry

## MLflow Model Registry

### Model Stages

- **None** - Initial registration
- **Staging** - Testing phase
- **Production** - Production-ready models
- **Archived** - Deprecated models

### Model Promotion

- Promote models through stages in MLflow UI
- Use production stage for Analyzer service
- Archive old models when deprecated

## Troubleshooting

### Model Loading Issues

- Verify model is registered in MLflow
- Check model URI format: `models:/{model_name}/latest`
- Ensure model extends `mlflow.pyfunc.PythonModel`
- Verify `predict()` method signature

### Training Issues

- Check MLflow connection: `MLFLOW_TRACKING_URI`
- Verify training data format
- Check model dependencies are logged
- Review MLflow run logs
