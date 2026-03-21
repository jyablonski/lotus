"""Training (registration) script for the semantic journal topic extractor.

There is no gradient-based training here — we use a pre-trained sentence-transformer
model (all-mpnet-base-v2) as-is. This script:

  1. Downloads and saves the sentence-transformer model to a temp directory.
  2. Serialises the topic hierarchy and model config as JSON artifacts.
  3. Runs a validation pass against sample journal entries to confirm the
     pyfunc wrapper works end-to-end before registering.
  4. Logs everything to MLflow and registers the model as "semantic_journal_topics".

Run inside Docker (or with MLflow reachable at MLFLOW_CONN_URI):
    uv run python -m src.training.train_topics_semantic
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Any

import mlflow
import mlflow.pyfunc
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sample journal entries for validation
# ---------------------------------------------------------------------------

_SAMPLE_ENTRIES: list[dict[str, str]] = [
    {
        "label": "work stress",
        "text": (
            "Had three back-to-back meetings today and still couldn't finish the "
            "report my manager needs by Friday. Feeling completely drained and "
            "overwhelmed by everything on my plate."
        ),
    },
    {
        "label": "gratitude / relationships",
        "text": (
            "Spent the evening cooking dinner with my partner. We laughed a lot "
            "and just enjoyed being present together. Feeling so grateful for "
            "moments like these."
        ),
    },
    {
        "label": "health / fitness",
        "text": (
            "Ran 5k this morning for the first time in months. My knee held up "
            "fine and I felt great afterwards. Going to try to make this a habit "
            "three times a week."
        ),
    },
    {
        "label": "anxiety / mental health",
        "text": (
            "Woke up at 3am again with racing thoughts about the future. Hard to "
            "shake this constant low-level anxiety. Need to figure out a better "
            "way to wind down before bed."
        ),
    },
    {
        "label": "short entry",
        "text": "Tough day. Need sleep.",
    },
    {
        "label": "creativity",
        "text": (
            "Finished the first draft of the short story I've been working on for "
            "two months. Really proud of how the ending came together. Can't wait "
            "to share it with my writing group."
        ),
    },
    {
        "label": "personal growth",
        "text": (
            "Started reading Atomic Habits. Already rethinking how I approach my "
            "morning routine. Small changes really do compound over time."
        ),
    },
    {
        "label": "sports",
        "text": "The Lakers won last night. LeBron was incredible.",
    },
]


# ---------------------------------------------------------------------------
# MLflow pyfunc wrapper
#
# Intentionally self-contained: no imports from src.models.*.
# All extraction logic is implemented inline so that MLflow can load this
# wrapper in the analyzer without needing code_paths or sys.path manipulation.
# ---------------------------------------------------------------------------


class SemanticTopicExtractorWrapper(mlflow.pyfunc.PythonModel):
    """MLflow pyfunc wrapper for the semantic journal topic extractor.

    Self-contained: loads a SentenceTransformer + KeyBERT directly from
    artifacts and implements extraction inline. No imports from src.models
    are needed, so this wrapper loads correctly in any environment that has
    keybert and sentence-transformers installed.

    Loaded artifacts (set by load_context):
        sentence_transformer  — directory containing the saved ST model
        hierarchy             — JSON file with the domain → subtopic mapping
        model_config          — JSON file with hyperparameters
    """

    def __getstate__(self) -> dict:
        # MLflow 3.x calls load_context() on the python_model instance during
        # log_model() validation *before* pickling it into python_model.pkl.
        # All runtime state is rebuilt from artifacts by load_context(), so we
        # return an empty state to keep python_model.pkl device-agnostic.
        return {}

    def __setstate__(self, state: dict) -> None:
        pass  # load_context() will populate all attributes at load time

    def load_context(self, context: mlflow.pyfunc.PythonModelContext) -> None:
        from keybert import KeyBERT
        from sentence_transformers import SentenceTransformer
        import torch

        with open(context.artifacts["hierarchy"]) as f:
            hierarchy: dict[str, list[str]] = json.load(f)

        with open(context.artifacts["model_config"]) as f:
            config: dict[str, Any] = json.load(f)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading sentence-transformer model from artifacts (device=%s)...", device)

        # Build flat taxonomy and reverse domain lookup from the saved hierarchy.
        self._taxonomy: list[str] = [sub for subs in hierarchy.values() for sub in subs]
        self._subtopic_to_domain: dict[str, str] = {
            sub: domain for domain, subs in hierarchy.items() for sub in subs
        }
        self._min_confidence: float = config["min_confidence"]
        self._min_cosine_similarity: float = config.get("min_cosine_similarity", 0.35)

        self._sentence_model = SentenceTransformer(context.artifacts["sentence_transformer"])
        self._kw_model = KeyBERT(model=self._sentence_model)

        # Precompute and cache taxonomy embeddings once at load time.
        self._taxonomy_embeddings: np.ndarray = self._sentence_model.encode(
            self._taxonomy,
            convert_to_tensor=False,
            normalize_embeddings=True,
        )

        logger.info(
            "SemanticTopicExtractorWrapper loaded: %d domains, %d subtopics",
            len(hierarchy),
            len(self._taxonomy),
        )

    def _extract_topics(self, text: str) -> list[dict]:
        """Extract hierarchical topics for a single journal entry."""
        word_count = len(text.split())
        top_n = 2 if word_count < 20 else (4 if word_count < 50 else 6)

        keyphrases: list[tuple[str, float]] = self._kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            top_n=top_n,
        )
        keyphrases = [(kp, score) for kp, score in keyphrases if score >= self._min_confidence]

        if not keyphrases:
            return []

        best: dict[str, tuple[str, float]] = {}  # subtopic → (domain, confidence)

        for keyphrase, kp_score in keyphrases:
            embedding = self._sentence_model.encode(keyphrase, normalize_embeddings=True)

            # Cosine similarity against precomputed taxonomy embeddings.
            vec = embedding.flatten()
            matrix = self._taxonomy_embeddings
            similarities = (matrix @ vec).flatten()

            best_idx = int(np.argmax(similarities))
            cosim = float(similarities[best_idx])

            # Skip if the best taxonomy match is too weak.
            if cosim < self._min_cosine_similarity:
                continue

            combined = round((kp_score + cosim) / 2, 4)
            subtopic = self._taxonomy[best_idx]
            domain = self._subtopic_to_domain[subtopic]

            if subtopic not in best or combined > best[subtopic][1]:
                best[subtopic] = (domain, combined)

        return sorted(
            [
                {"topic_name": domain, "subtopic_name": subtopic, "confidence": conf}
                for subtopic, (domain, conf) in best.items()
            ],
            key=lambda t: t["confidence"],
            reverse=True,
        )

    def predict(
        self,
        context: mlflow.pyfunc.PythonModelContext,
        model_input: pd.DataFrame,
    ) -> list[dict]:
        """Extract hierarchical topics for each row in model_input.

        Args:
            model_input: DataFrame with a ``"text"`` column.

        Returns:
            List of dicts (one per row)::

                [
                    {
                        "topics": [
                            {
                                "topic_name": "work",
                                "subtopic_name": "deadlines and workload pressure",
                                "confidence": 0.8731,
                            },
                            ...,
                        ]
                    },
                    ...,
                ]
        """
        if "text" not in model_input.columns:
            raise ValueError("model_input must contain a 'text' column")

        return [{"topics": self._extract_topics(text)} for text in model_input["text"].tolist()]


# ---------------------------------------------------------------------------
# Registration entrypoint
# ---------------------------------------------------------------------------


def train_and_register() -> None:
    from sentence_transformers import SentenceTransformer

    # Import hierarchy from src.models — safe here because train_and_register()
    # runs on the host where experiments/src/ is on sys.path.
    from src.models.semantic_topic_extractor import (
        JOURNAL_TOPIC_HIERARCHY,
        JOURNAL_TOPIC_TAXONOMY,
    )

    mlflow_uri = os.getenv("MLFLOW_CONN_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment("journal_topic_extraction")

    model_name = "all-mpnet-base-v2"
    config = {
        "model_name": model_name,
        "min_confidence": 0.25,
        "min_cosine_similarity": 0.35,
    }

    with mlflow.start_run(run_name="semantic_topic_extractor") as run:
        mlflow.log_params(config)
        mlflow.log_param("taxonomy_domains", len(JOURNAL_TOPIC_HIERARCHY))
        mlflow.log_param("taxonomy_subtopics", len(JOURNAL_TOPIC_TAXONOMY))

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Save sentence-transformer model.
            st_path = os.path.join(tmpdir, "sentence_transformer")
            logger.info("Downloading and saving sentence-transformer model: %s", model_name)
            SentenceTransformer(model_name).save(st_path)

            # 2. Save hierarchy (domain → subtopic list mapping).
            hierarchy_path = os.path.join(tmpdir, "hierarchy.json")
            with open(hierarchy_path, "w") as f:
                json.dump(JOURNAL_TOPIC_HIERARCHY, f, indent=2)

            # 3. Save model config.
            config_path = os.path.join(tmpdir, "model_config.json")
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            artifacts = {
                "sentence_transformer": st_path,
                "hierarchy": hierarchy_path,
                "model_config": config_path,
            }

            # 4. Validate the wrapper end-to-end before registering.
            logger.info("Running validation pass on sample entries...")
            wrapper = SemanticTopicExtractorWrapper()
            wrapper.load_context(  # type: ignore[arg-type]
                type("Ctx", (), {"artifacts": artifacts})()
            )

            validation_df = pd.DataFrame({"text": [entry["text"] for entry in _SAMPLE_ENTRIES]})
            results = wrapper.predict(None, validation_df)  # type: ignore[arg-type]

            for entry, result in zip(_SAMPLE_ENTRIES, results, strict=True):
                topics = result["topics"]
                top = topics[0] if topics else {}
                logger.info(
                    "[%s] → %d topics, top: %s / %s (%.3f)",
                    entry["label"],
                    len(topics),
                    top.get("topic_name", "(none)"),
                    top.get("subtopic_name", "(none)"),
                    top.get("confidence", 0.0),
                )
                mlflow.log_metric(
                    f"val_topics_{entry['label'].replace(' / ', '_').replace(' ', '_')}",
                    len(topics),
                )

            # 5. Log and register the pyfunc model.
            # No code_paths needed — the wrapper is self-contained and only
            # uses installed packages (keybert, sentence-transformers, numpy).
            logger.info("Logging model to MLflow...")
            mlflow.pyfunc.log_model(
                artifact_path="model",
                python_model=SemanticTopicExtractorWrapper(),
                artifacts=artifacts,
                pip_requirements=[
                    "keybert>=0.8.5",
                    "sentence-transformers>=3.0.0",
                ],
                registered_model_name="semantic_journal_topics",
            )

        logger.info("Registered 'semantic_journal_topics', run_id=%s", run.info.run_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_and_register()
