"""Semantic topic extractor for journal entries using sentence-transformers.

Embeds the full journal text and compares it directly against precomputed
taxonomy label embeddings using cosine similarity.  This approach preserves
full sentence context (no lossy keyphrase extraction step) and works well
for both short and long entries.
"""

from __future__ import annotations

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
    """Extracts semantic topics from journal text using sentence-transformers.

    Embeds the full journal text and ranks all taxonomy labels by cosine
    similarity.  No keyphrase extraction step — full context is preserved.

    Args:
        model_name: HuggingFace sentence-transformer model identifier.
        taxonomy: List of canonical topic strings. Defaults to JOURNAL_TOPIC_TAXONOMY.
        min_confidence: Minimum cosine similarity to include a topic (0-1).
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        taxonomy: list[str] | None = None,
        min_confidence: float = 0.20,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.taxonomy = taxonomy if taxonomy is not None else JOURNAL_TOPIC_TAXONOMY
        self.min_confidence = min_confidence

        self.sentence_model = SentenceTransformer(model_name)

        # Precompute and cache taxonomy embeddings once at init time.
        self.taxonomy_embeddings = self.sentence_model.encode(
            self.taxonomy,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )

    def _max_topics(self, word_count: int) -> int:
        """Scale the topic budget with entry length, up to 7."""
        if word_count < 15:
            return 2
        if word_count < 40:
            return 4
        if word_count < 80:
            return 5
        if word_count < 150:
            return 6
        return 7

    def extract_topics(self, text: str) -> list[dict]:
        """Extract canonical topics from a single journal entry.

        Args:
            text: Raw journal entry text.

        Returns:
            List of topic dicts sorted by descending confidence:
            [{"topic_name": str, "confidence": float}, ...]
        """
        from sentence_transformers import util

        word_count = len(text.split())
        max_topics = self._max_topics(word_count)

        # Embed the full text and compare directly to every taxonomy label.
        text_embedding = self.sentence_model.encode(
            text,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )
        similarities = util.cos_sim(text_embedding, self.taxonomy_embeddings)[0]

        top_k = min(max_topics, len(self.taxonomy))
        top_values, top_indices = similarities.topk(top_k)

        return [
            {"topic_name": self.taxonomy[int(idx)], "confidence": round(float(val), 4)}
            for val, idx in zip(top_values, top_indices, strict=True)
            if float(val) >= self.min_confidence
        ]

    def extract_topics_batch(self, texts: list[str]) -> list[list[dict]]:
        """Extract topics for multiple journal entries."""
        return [self.extract_topics(text) for text in texts]
