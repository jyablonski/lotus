"""Semantic topic extractor for journal entries using KeyBERT + sentence-transformers.

Extracts keyphrases from the journal text using KeyBERT, then maps each
keyphrase to the nearest canonical subtopic label via cosine similarity.
Topics are returned as (domain, subtopic) pairs — the domain is the
broad life area and the subtopic is the more precise, descriptive label
that was actually matched.  Confidence is the average of the KeyBERT
extraction score and the cosine similarity.
"""

from __future__ import annotations

from keybert import KeyBERT
import numpy as np
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Hierarchical taxonomy
#
# Top-level keys are broad life domains stored as topic_name in the DB.
# Values are lists of descriptive subtopic labels used for embedding
# and cosine-similarity matching — longer phrases give the model more
# semantic surface area than single-word labels.
# ---------------------------------------------------------------------------

JOURNAL_TOPIC_HIERARCHY: dict[str, list[str]] = {
    "work": [
        "deadlines and workload pressure",
        "career growth and ambition",
        "workplace relationships and colleagues",
        "job satisfaction and meaning",
        "work-life balance and boundaries",
    ],
    "family": [
        "parenting and raising children",
        "partnership and marriage",
        "family conflict and tension",
        "household chores and responsibilities",
        "extended family and relatives",
    ],
    "relationships": [
        "friendship and social connection",
        "romantic relationship and dating",
        "loneliness and social isolation",
        "conflict and disagreement with others",
    ],
    "health": [
        "physical illness and recovery",
        "diet and nutrition habits",
        "exercise and physical fitness",
        "medical care and health concerns",
    ],
    "sleep": [
        "sleep quality and insomnia",
        "fatigue and low energy",
        "rest and relaxation",
    ],
    "wellbeing": [
        "anxiety and worry about the future",
        "sadness and grief",
        "stress and feeling overwhelmed",
        "happiness and positive emotions",
        "anger and frustration",
        "emotional numbness and disconnection",
    ],
    "growth": [
        "learning and skill development",
        "self-reflection and introspection",
        "goals and personal motivation",
        "habits and daily discipline",
        "identity and self-worth",
    ],
    "finances": [
        "financial stress and debt",
        "spending and budgeting",
        "financial goals and savings",
    ],
    "creativity": [
        "creative projects and artistic expression",
        "hobbies and leisure activities",
        "entertainment and media consumption",
    ],
    "spirituality": [
        "spiritual practice and faith",
        "purpose and meaning in life",
        "gratitude and appreciation",
        "mindfulness and present-moment awareness",
    ],
    "travel": [
        "nature and outdoor experiences",
        "travel and new places",
        "food and eating experiences",
        "social events and community",
    ],
}

# Flat list of all subtopic strings — used as the embedding target vocabulary.
# Exposed as JOURNAL_TOPIC_TAXONOMY for backward compatibility with tests that
# reference this constant.
JOURNAL_TOPIC_TAXONOMY: list[str] = [
    subtopic for subtopics in JOURNAL_TOPIC_HIERARCHY.values() for subtopic in subtopics
]

# Module-level reverse lookup: subtopic label → parent domain name.
_SUBTOPIC_TO_DOMAIN: dict[str, str] = {
    subtopic: domain
    for domain, subtopics in JOURNAL_TOPIC_HIERARCHY.items()
    for subtopic in subtopics
}


class SemanticTopicExtractor:
    """Extracts hierarchical topics from journal text using KeyBERT + sentence-transformers.

    Keyphrases are extracted with KeyBERT, then each is mapped to the closest
    subtopic label via cosine similarity.  The parent domain is resolved via
    ``JOURNAL_TOPIC_HIERARCHY``.

    Each result entry contains:

    - ``topic_name``    — broad domain (e.g. ``"work"``)
    - ``subtopic_name`` — matched descriptive label
      (e.g. ``"deadlines and workload pressure"``)
    - ``confidence``    — ``(KeyBERT score + cosine similarity) / 2``,
      rounded to 4 decimal places

    Duplicate mappings to the same subtopic are collapsed, keeping the
    highest combined confidence.

    Args:
        model_name: HuggingFace sentence-transformer model identifier.
            Defaults to ``all-mpnet-base-v2`` (768-dim, higher quality than
            the 384-dim ``all-MiniLM-L6-v2``).
        taxonomy: Flat list of subtopic strings to embed and match against.
            Defaults to ``JOURNAL_TOPIC_TAXONOMY`` (all subtopics from the
            hierarchy).  Pass a custom list for experiments; when a label has
            no entry in the module-level domain map, ``topic_name`` falls back
            to the matched label string itself.
        min_confidence: Minimum KeyBERT extraction score to retain a
            keyphrase (0-1).
        keyphrase_ngram_range: n-gram range forwarded to KeyBERT.
    """

    def __init__(
        self,
        model_name: str = "all-mpnet-base-v2",
        taxonomy: list[str] | None = None,
        min_confidence: float = 0.15,
        keyphrase_ngram_range: tuple[int, int] = (1, 2),
    ) -> None:
        self.model_name = model_name
        self.taxonomy = taxonomy if taxonomy is not None else JOURNAL_TOPIC_TAXONOMY
        self.min_confidence = min_confidence
        self.keyphrase_ngram_range = keyphrase_ngram_range

        # Per-instance domain lookup.  Falls back to the subtopic string itself
        # when a custom (non-hierarchical) taxonomy is supplied.
        self._subtopic_to_domain: dict[str, str] = {
            t: _SUBTOPIC_TO_DOMAIN.get(t, t) for t in self.taxonomy
        }

        self.sentence_model = SentenceTransformer(model_name)
        self.kw_model = KeyBERT(model=self.sentence_model)

        # Precompute and cache subtopic embeddings once at init time.
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

        # Guard against dimension mismatch (e.g. when tests substitute mock
        # encoders that return a different embedding size than taxonomy_embeddings).
        if vec.shape[0] != self.taxonomy_embeddings.shape[1]:
            return np.zeros(len(self.taxonomy))

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
        """Extract hierarchical topics from a single journal entry.

        Args:
            text: Raw journal entry text.

        Returns:
            List of topic dicts sorted by descending confidence::

                [
                    {
                        "topic_name": "work",
                        "subtopic_name": "deadlines and workload pressure",
                        "confidence": 0.8731,
                    },
                    ...,
                ]
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

        # Map each keyphrase to its best-matching subtopic, then resolve the
        # parent domain.  Deduplicate per subtopic, keeping the highest score.
        best: dict[str, tuple[str, float]] = {}  # subtopic → (domain, confidence)

        for keyphrase, kp_score in keyphrases:
            embedding = self.sentence_model.encode(keyphrase, normalize_embeddings=True)
            similarities = self._cosine_similarities(embedding)
            best_idx = int(np.argmax(similarities))
            cosim = float(similarities[best_idx])
            combined = round((kp_score + cosim) / 2, 4)
            subtopic = self.taxonomy[best_idx]
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

    def extract_topics_batch(self, texts: list[str]) -> list[list[dict]]:
        """Extract topics for multiple journal entries."""
        return [self.extract_topics(text) for text in texts]
