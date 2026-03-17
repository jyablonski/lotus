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
]


# ---------------------------------------------------------------------------
# MLflow pyfunc wrapper
# ---------------------------------------------------------------------------


class SemanticTopicExtractorWrapper(mlflow.pyfunc.PythonModel):
    """MLflow pyfunc wrapper around SemanticTopicExtractor.

    Loaded artifacts (set by load_context):
        sentence_transformer  — directory containing the saved ST model
        taxonomy_labels       — JSON file with the canonical topic list
        model_config          — JSON file with hyperparameters
    """

    def load_context(self, context: mlflow.pyfunc.PythonModelContext) -> None:
        from keybert import KeyBERT
        from sentence_transformers import SentenceTransformer

        logger.info("Loading sentence-transformer model from artifacts...")
        self.sentence_model = SentenceTransformer(context.artifacts["sentence_transformer"])
        self.kw_model = KeyBERT(model=self.sentence_model)

        with open(context.artifacts["taxonomy_labels"]) as f:
            self.taxonomy: list[str] = json.load(f)

        # Precompute taxonomy embeddings once at load time.
        self.taxonomy_embeddings = self.sentence_model.encode(
            self.taxonomy,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )

        with open(context.artifacts["model_config"]) as f:
            config: dict[str, Any] = json.load(f)

        self.keyphrase_ngram_range: tuple[int, int] = tuple(  # type: ignore[assignment]
            config["keyphrase_ngram_range"]
        )
        self.min_confidence: float = config["min_confidence"]

        logger.info(
            "SemanticTopicExtractorWrapper loaded: taxonomy_size=%d, ngram_range=%s",
            len(self.taxonomy),
            self.keyphrase_ngram_range,
        )

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

            if word_count < 20:
                top_n = 2
            elif word_count < 50:
                top_n = 4
            else:
                top_n = 6

            keyphrases: list[tuple[str, float]] = self.kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=self.keyphrase_ngram_range,
                stop_words="english",
                use_maxsum=True,
                nr_candidates=20,
                top_n=top_n,
            )

            seen_topics: dict[str, float] = {}

            for phrase, keyphrase_score in keyphrases:
                if keyphrase_score < self.min_confidence:
                    continue

                phrase_embedding = self.sentence_model.encode(
                    phrase,
                    convert_to_tensor=True,
                    normalize_embeddings=True,
                )
                similarities = util.cos_sim(phrase_embedding, self.taxonomy_embeddings)[0]
                best_idx = int(similarities.argmax())
                taxonomy_score = float(similarities[best_idx])

                topic_name = self.taxonomy[best_idx]
                combined_score = (keyphrase_score + taxonomy_score) / 2

                if topic_name not in seen_topics or combined_score > seen_topics[topic_name]:
                    seen_topics[topic_name] = combined_score

            topics = [
                {"topic_name": name, "confidence": round(score, 4)}
                for name, score in sorted(seen_topics.items(), key=lambda x: x[1], reverse=True)
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
        "keyphrase_ngram_range": [1, 2],
        "min_confidence": 0.15,
        "nr_candidates": 20,
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
                    "keybert>=0.8.5",
                    "sentence-transformers>=3.0.0",
                ],
                registered_model_name="semantic_journal_topics",
            )

        logger.info("Registered 'semantic_journal_topics', run_id=%s", run.info.run_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_and_register()
