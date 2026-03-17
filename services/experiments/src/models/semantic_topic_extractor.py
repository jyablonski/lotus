"""Semantic topic extractor for journal entries using KeyBERT + sentence-transformers.

Extracts keyphrases from the journal text using KeyBERT, then maps each
keyphrase to the nearest canonical taxonomy label via cosine similarity.
The per-topic confidence is the average of the KeyBERT extraction score
and the cosine similarity, giving a balanced signal from both extraction
quality and semantic alignment.
"""

from __future__ import annotations

from keybert import KeyBERT
import numpy as np
from sentence_transformers import SentenceTransformer

JOURNAL_TOPIC_TAXONOMY: list[str] = [
    # Life domains
    "work",
    "family",
    "relationships",
    "health",
    "fitness",
    "sleep",
    "money",
    "creativity",
    "hobbies",
    "sports",
    "travel",
    "nature",
    "food",
    # Emotional states
    "gratitude",
    "sadness",
    "anxiety",
    "stress",
    "motivation",
    "happiness",
    "love",
    "anger",
    "loneliness",
    # Life themes
    "achievement",
    "growth",
    "learning",
    "productivity",
    "parenting",
    "spirituality",
    "reflection",
]


class SemanticTopicExtractor:
    """Extracts semantic topics from journal text using KeyBERT + sentence-transformers.

    Keyphrases are extracted with KeyBERT, then each is mapped to the closest
    taxonomy label via cosine similarity.  Confidence = (keyphrase_score +
    cosine_similarity) / 2, rounded to 4 decimal places.  Duplicate mappings
    to the same taxonomy entry are collapsed, keeping the highest confidence.

    Args:
        model_name: HuggingFace sentence-transformer model identifier.
        taxonomy: List of canonical topic strings. Defaults to JOURNAL_TOPIC_TAXONOMY.
        min_confidence: Minimum KeyBERT extraction score to retain a keyphrase (0-1).
        keyphrase_ngram_range: n-gram range forwarded to KeyBERT.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        taxonomy: list[str] | None = None,
        min_confidence: float = 0.15,
        keyphrase_ngram_range: tuple[int, int] = (1, 2),
    ) -> None:
        self.model_name = model_name
        self.taxonomy = taxonomy if taxonomy is not None else JOURNAL_TOPIC_TAXONOMY
        self.min_confidence = min_confidence
        self.keyphrase_ngram_range = keyphrase_ngram_range

        self.sentence_model = SentenceTransformer(model_name)
        self.kw_model = KeyBERT(model=self.sentence_model)

        # Precompute and cache taxonomy embeddings once at init time.
        self.taxonomy_embeddings: np.ndarray = self.sentence_model.encode(
            self.taxonomy,
            convert_to_tensor=False,
            normalize_embeddings=True,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _top_n(self, word_count: int) -> int:
        """Adaptive keyphrase budget scaled to entry length."""
        if word_count < 20:
            return 2
        if word_count < 50:
            return 4
        return 6

    def _cosine_similarities(self, vec: np.ndarray) -> np.ndarray:
        """Cosine similarity between *vec* and every row of taxonomy_embeddings."""
        if vec.ndim == 2:
            vec = vec[0]
        vec_norm = np.linalg.norm(vec)
        if vec_norm == 0.0:
            return np.zeros(len(self.taxonomy))
        vec_unit = vec / vec_norm

        matrix = self.taxonomy_embeddings
        row_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        row_norms = np.where(row_norms == 0.0, 1.0, row_norms)
        matrix_unit = matrix / row_norms

        return (matrix_unit @ vec_unit).flatten()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_topics(self, text: str) -> list[dict]:
        """Extract canonical topics from a single journal entry.

        Args:
            text: Raw journal entry text.

        Returns:
            List of topic dicts sorted by descending confidence:
            [{"topic_name": str, "confidence": float}, ...]
        """
        word_count = len(text.split())
        top_n = self._top_n(word_count)

        keyphrases: list[tuple[str, float]] = self.kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=self.keyphrase_ngram_range,
            top_n=top_n,
        )

        # Filter keyphrases below the minimum extraction confidence.
        keyphrases = [(kp, score) for kp, score in keyphrases if score >= self.min_confidence]

        if not keyphrases:
            return []

        # Map each keyphrase to the best-matching taxonomy entry, deduplicating
        # by keeping the highest combined confidence per taxonomy label.
        best: dict[str, float] = {}
        for keyphrase, kp_score in keyphrases:
            embedding = self.sentence_model.encode(keyphrase, normalize_embeddings=True)
            similarities = self._cosine_similarities(embedding)
            best_idx = int(np.argmax(similarities))
            cosim = float(similarities[best_idx])
            combined = round((kp_score + cosim) / 2, 4)
            label = self.taxonomy[best_idx]
            if label not in best or combined > best[label]:
                best[label] = combined

        return sorted(
            [{"topic_name": label, "confidence": conf} for label, conf in best.items()],
            key=lambda t: t["confidence"],
            reverse=True,
        )

    def extract_topics_batch(self, texts: list[str]) -> list[list[dict]]:
        """Extract topics for multiple journal entries."""
        return [self.extract_topics(text) for text in texts]
