"""Training (registration) script for the semantic journal topic extractor.

There is no gradient-based training here — we use a pre-trained sentence-transformer
model (all-MiniLM-L6-v2) as-is. This script:

  1. Downloads and saves the sentence-transformer model to a temp directory.
  2. Serialises the topic taxonomy and model config as JSON artifacts.
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
import pandas as pd

from src.models.semantic_topic_extractor import JOURNAL_TOPIC_TAXONOMY

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
# ---------------------------------------------------------------------------


class SemanticTopicExtractorWrapper(mlflow.pyfunc.PythonModel):
    """MLflow pyfunc wrapper for the semantic journal topic extractor.

    Embeds the full journal text directly and ranks taxonomy labels by cosine
    similarity — no intermediate keyphrase extraction step.

    Loaded artifacts (set by load_context):
        sentence_transformer  — directory containing the saved ST model
        taxonomy_labels       — JSON file with the canonical topic list
        model_config          — JSON file with hyperparameters
    """

    def __getstate__(self) -> dict:
        # MLflow 3.x calls load_context() on the python_model instance during
        # log_model() validation *before* pickling it into python_model.pkl.
        # All runtime state (sentence_model, taxonomy_embeddings, …) is rebuilt
        # from artifacts by load_context(), so we return an empty pickle state
        # to keep python_model.pkl device-agnostic.
        return {}

    def __setstate__(self, state: dict) -> None:
        pass  # load_context() will populate all attributes at load time

    def load_context(self, context: mlflow.pyfunc.PythonModelContext) -> None:
        from sentence_transformers import SentenceTransformer
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading sentence-transformer model from artifacts (device=%s)...", device)
        self.sentence_model = SentenceTransformer(
            context.artifacts["sentence_transformer"], device=device
        )

        with open(context.artifacts["taxonomy_labels"]) as f:
            self.taxonomy: list[str] = json.load(f)

        # Precompute taxonomy embeddings once. Store on CPU so that if MLflow
        # pickles this instance for validation, no CUDA tensors end up in
        # python_model.pkl. predict() moves them to the right device on demand.
        self.taxonomy_embeddings = self.sentence_model.encode(
            self.taxonomy,
            convert_to_tensor=True,
            normalize_embeddings=True,
        ).cpu()

        with open(context.artifacts["model_config"]) as f:
            config: dict[str, Any] = json.load(f)

        self.min_confidence: float = config["min_confidence"]

        logger.info(
            "SemanticTopicExtractorWrapper loaded: taxonomy_size=%d, device=%s",
            len(self.taxonomy),
            device,
        )

    @staticmethod
    def _max_topics(word_count: int) -> int:
        """Scale topic budget with entry length, up to 7."""
        if word_count < 15:
            return 2
        if word_count < 40:
            return 4
        if word_count < 80:
            return 5
        if word_count < 150:
            return 6
        return 7

    def predict(
        self,
        context: mlflow.pyfunc.PythonModelContext,
        model_input: pd.DataFrame,
    ) -> list[dict]:
        """Extract canonical topics for each row in model_input.

        Args:
            model_input: DataFrame with a "text" column.

        Returns:
            List of dicts (one per row):
            [{"topics": [{"topic_name": str, "confidence": float}, ...]}, ...]
        """
        from sentence_transformers import util

        if "text" not in model_input.columns:
            raise ValueError("model_input must contain a 'text' column")

        results: list[dict] = []

        for text in model_input["text"].tolist():
            word_count = len(text.split())
            max_topics = self._max_topics(word_count)

            # Embed the full text and compare directly to every taxonomy label.
            # This preserves full sentence context — "I love basketball" maps to
            # sports, not love/romance, because the whole sentence is encoded.
            text_embedding = self.sentence_model.encode(
                text,
                convert_to_tensor=True,
                normalize_embeddings=True,
            )
            taxonomy_embs = self.taxonomy_embeddings.to(text_embedding.device)
            similarities = util.cos_sim(text_embedding, taxonomy_embs)[0]

            top_k = min(max_topics, len(self.taxonomy))
            top_values, top_indices = similarities.topk(top_k)

            topics = [
                {"topic_name": self.taxonomy[int(idx)], "confidence": round(float(val), 4)}
                for val, idx in zip(top_values, top_indices, strict=True)
                if float(val) >= self.min_confidence
            ]
            results.append({"topics": topics})

        return results


# ---------------------------------------------------------------------------
# Registration entrypoint
# ---------------------------------------------------------------------------


def train_and_register() -> None:
    from sentence_transformers import SentenceTransformer

    mlflow_uri = os.getenv("MLFLOW_CONN_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment("journal_topic_extraction")

    model_name = "all-MiniLM-L6-v2"
    config = {
        "model_name": model_name,
        "min_confidence": 0.12,
    }

    with mlflow.start_run(run_name="semantic_topic_extractor") as run:
        mlflow.log_params(config)
        mlflow.log_param("taxonomy_size", len(JOURNAL_TOPIC_TAXONOMY))

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Save sentence-transformer model.
            st_path = os.path.join(tmpdir, "sentence_transformer")
            logger.info("Downloading and saving sentence-transformer model: %s", model_name)
            SentenceTransformer(model_name).save(st_path)

            # 2. Save taxonomy labels.
            taxonomy_path = os.path.join(tmpdir, "taxonomy_labels.json")
            with open(taxonomy_path, "w") as f:
                json.dump(JOURNAL_TOPIC_TAXONOMY, f, indent=2)

            # 3. Save model config.
            config_path = os.path.join(tmpdir, "model_config.json")
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            artifacts = {
                "sentence_transformer": st_path,
                "taxonomy_labels": taxonomy_path,
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
                top = topics[0]["topic_name"] if topics else "(none)"
                logger.info(
                    "[%s] → %d topics, top: %s (%.3f)",
                    entry["label"],
                    len(topics),
                    top,
                    topics[0]["confidence"] if topics else 0.0,
                )
                mlflow.log_metric(
                    f"val_topics_{entry['label'].replace(' / ', '_').replace(' ', '_')}",
                    len(topics),
                )

            # 5. Log and register the pyfunc model.
            logger.info("Logging model to MLflow...")
            mlflow.pyfunc.log_model(
                artifact_path="model",
                python_model=SemanticTopicExtractorWrapper(),
                artifacts=artifacts,
                pip_requirements=[
                    "sentence-transformers>=3.0.0",
                ],
                registered_model_name="semantic_journal_topics",
            )

        logger.info("Registered 'semantic_journal_topics', run_id=%s", run.info.run_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_and_register()
