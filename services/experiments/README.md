# Experiments

Machine learning models and training scripts for extracting topics and sentiment from journal entries. Models are trained here, pushed to MLflow, and loaded at runtime by the analyzer service.

## Structure

```
experiments/
├── src/
│   ├── models/
│   │   ├── semantic_topic_extractor.py   # SemanticTopicExtractor (KeyBERT + sentence-transformers)
│   │   └── sentiment_analyzer.py        # JournalSentimentAnalyzer (sklearn)
│   └── training/
│       ├── train_topics_semantic.py     # Registers semantic_journal_topics in MLflow
│       ├── train_sentiment_analysis.py  # Registers journal_sentiment_analyzer in MLflow
│       ├── train_article_recommender.py
│       └── train_example.py
└── README.md
```

## Quick Start

```bash
# spin up full stack with MLflow
make up

cd services/experiments/

# register the semantic topic model (downloads ~420 MB sentence-transformer on first run)
uv run python -m src.training.train_topics_semantic

# register the sentiment model
uv run python -m src.training.train_sentiment_analysis
```

After running, restart the analyzer service so it picks up the new model versions.

---

## How the MLflow Integration Works

### The pyfunc wrapper pattern

Every model registered here follows the same pattern:

1. **A `PythonModel` subclass** in the training script wraps the underlying model
2. **`load_context()`** is called once when MLflow loads the model — this is where you reconstruct the model from saved artifacts (weights files, JSON configs, etc.)
3. **`predict()`** is called per-request in the analyzer — it takes a pandas DataFrame with a `"text"` column and returns a list of dicts

```python
class MyModelWrapper(mlflow.pyfunc.PythonModel):

    def load_context(self, context: mlflow.pyfunc.PythonModelContext) -> None:
        # Runs once at analyzer startup.
        # context.artifacts is a dict of {name: local_path} for everything
        # you passed in the artifacts={} dict when logging the model.
        with open(context.artifacts["my_config"]) as f:
            config = json.load(f)
        self.model = load_my_model(context.artifacts["model_weights"], config)

    def predict(self, context, model_input: pd.DataFrame) -> list[dict]:
        # Runs on every inference request.
        # Must accept a DataFrame with at least a "text" column.
        # Must return a list of dicts — one per row.
        results = []
        for text in model_input["text"].tolist():
            results.append({"topics": self.model.extract(text)})
        return results
```

### Registering the model

```python
mlflow.pyfunc.log_model(
    artifact_path="model",
    python_model=MyModelWrapper(),
    artifacts={
        "model_weights": "/tmp/weights/",   # local path at training time
        "my_config":     "/tmp/config.json",
    },
    code_paths=["src"],                     # bundles experiments/src/ with the model
    pip_requirements=[
        "keybert>=0.8.5",
        "sentence-transformers>=3.0.0",
    ],
    registered_model_name="my_model_name",  # must match what the analyzer client uses
)
```

**`code_paths=["src"]` is required** whenever your wrapper imports anything from `src/` (e.g. `from src.models.semantic_topic_extractor import SemanticTopicExtractor`). MLflow bundles the `src/` directory into the model artifact and adds it to `sys.path` when loading the model in the analyzer. Without it the analyzer will raise a `ModuleNotFoundError` at startup.

### What the analyzer expects from `predict()`

The analyzer's `BaseMLflowClient` calls `self.model.predict(dataframe)` directly. Each specific client (`TopicClient`, `SentimentClient`) then shapes the raw output into the format it needs. The contract for topic models:

```python
# Input — always a DataFrame with a "text" column
model_input = pd.DataFrame({"text": ["journal entry text..."]})

# Output — list of dicts, one per row, each with a "topics" key
[
    {
        "topics": [
            {
                "topic_name":    "work and career",
                "subtopic_name": "deadlines and workload pressure",
                "confidence":    0.8731,
            },
            ...
        ]
    }
]
```

---

## Dependencies: Experiments vs Analyzer

The two services **do not need identical dependencies**, but they need to agree on the runtime packages the model actually uses during inference.

| Concern                                                  | How it's handled                                                                               |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Wrapper source code (`src/models/`)                      | Bundled into the MLflow artifact via `code_paths=["src"]` — no install needed in analyzer      |
| Inference libraries (`keybert`, `sentence-transformers`) | Listed in `pip_requirements` when logging — **must also be installed in the analyzer service** |
| Training-only libraries (`scikit-learn`, `pandas`)       | Only needed in experiments, not in the analyzer                                                |
| MLflow version                                           | Should match — both pinned to `>=3.3.2`. Mismatches produce a warning at load time             |

The practical rule: anything your `predict()` method imports at runtime must be in both `pip_requirements` (logged with the model) and the analyzer's `pyproject.toml`. Anything only used during training or in `train_and_register()` only needs to be in experiments.

---

## Performance: Sentence-Transformer Models

Sentence-transformer models are large and have a real startup cost. This matters because the analyzer loads models synchronously at startup and blocks until they are ready.

| Model                           | Size on disk | Load time (CPU) | Embedding dim | Quality |
| ------------------------------- | ------------ | --------------- | ------------- | ------- |
| `all-MiniLM-L6-v2`              | ~90 MB       | ~2–3 s          | 384           | Good    |
| `all-mpnet-base-v2` _(current)_ | ~420 MB      | ~8–15 s         | 768           | Better  |
| `all-roberta-large-v1`          | ~1.3 GB      | ~30–60 s        | 1024          | Best    |

**Current model**: `all-mpnet-base-v2` — 420 MB stored in the MLflow artifact, ~8–15 seconds to load on CPU at analyzer startup. Inference per journal entry (KeyBERT keyphrase extraction + cosine similarity) is roughly 200–500 ms on CPU depending on text length.

Things that affect startup time:

- **Artifact download** — if MLflow is on a remote server, the ~420 MB weights transfer over the network on first load (subsequently cached locally)
- **CPU vs GPU** — sentence-transformers load significantly faster on GPU and inference is ~10–20× faster; the current setup runs CPU-only
- **KeyBERT initialisation** — KeyBERT wraps the same sentence-transformer instance, so there is no second model to load

If startup time becomes a problem, the main lever is switching back to `all-MiniLM-L6-v2` in `train_topics_semantic.py` — it is 5× smaller and loads in a third of the time with a modest quality trade-off.
