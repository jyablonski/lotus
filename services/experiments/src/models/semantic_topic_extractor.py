"""Semantic topic extractor for journal entries using KeyBERT + sentence-transformers.

Uses a pre-trained sentence transformer model (no fine-tuning required) to extract
semantically meaningful keyphrases and map them to a canonical topic taxonomy.

Two-stage approach:
  1. KeyBERT extracts the most representative n-gram keyphrases from the text using
     cosine similarity between candidate phrase embeddings and the document embedding.
  2. Each keyphrase is mapped to the closest entry in a canonical topic taxonomy via
     cosine similarity between their sentence-transformer embeddings.

This replaces the old TF-IDF + LDA approach with a fully semantic pipeline that
understands meaning rather than just word frequency.
"""

from __future__ import annotations

JOURNAL_TOPIC_TAXONOMY: list[str] = [
    # Life domains
    "work and career",
    "relationships and social life",
    "family",
    "mental health and anxiety",
    "physical health and fitness",
    "sleep and rest",
    "finances and money",
    "personal growth and self-improvement",
    "creativity and art",
    "hobbies and leisure",
    "travel and adventure",
    "food and nutrition",
    # Emotional states
    "gratitude and appreciation",
    "sadness and grief",
    "stress and overwhelm",
    "motivation and goals",
    "joy and happiness",
    "love and romance",
    "conflict and frustration",
    "loneliness and isolation",
    # Life events / themes
    "achievement and success",
    "daily routine",
    "reflection and introspection",
    "spirituality and mindfulness",
    "learning and education",
    "parenting and children",
    "productivity and time management",
]


class SemanticTopicExtractor:
    """Extracts semantic topics from journal text using KeyBERT + sentence-transformers.

    Args:
        model_name: HuggingFace sentence-transformer model identifier.
        taxonomy: List of canonical topic strings to map keyphrases onto.
            Defaults to JOURNAL_TOPIC_TAXONOMY.
        keyphrase_ngram_range: Min/max word count for extracted keyphrases.
        min_confidence: Minimum combined confidence score to include a topic.
            Combined score = average of (keyphrase relevance, taxonomy similarity).
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        taxonomy: list[str] | None = None,
        keyphrase_ngram_range: tuple[int, int] = (1, 2),
        min_confidence: float = 0.15,
    ) -> None:
        from keybert import KeyBERT
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.taxonomy = taxonomy if taxonomy is not None else JOURNAL_TOPIC_TAXONOMY
        self.keyphrase_ngram_range = keyphrase_ngram_range
        self.min_confidence = min_confidence

        self.sentence_model = SentenceTransformer(model_name)
        self.kw_model = KeyBERT(model=self.sentence_model)

        # Precompute and cache taxonomy embeddings once at init time.
        self.taxonomy_embeddings = self.sentence_model.encode(
            self.taxonomy,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )

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

        # Adaptive keyphrase budget based on entry length.
        if word_count < 20:
            top_n = 2
        elif word_count < 50:
            top_n = 4
        else:
            top_n = 6

        # KeyBERT: extract top-n keyphrases most representative of the document.
        # use_maxsum=True diversifies results (Max Sum Similarity algorithm).
        keyphrases: list[tuple[str, float]] = self.kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=self.keyphrase_ngram_range,
            stop_words="english",
            use_maxsum=True,
            nr_candidates=20,
            top_n=top_n,
        )

        if not keyphrases:
            return []

        seen_topics: dict[str, float] = {}

        for phrase, keyphrase_score in keyphrases:
            if keyphrase_score < self.min_confidence:
                continue

            # Map the keyphrase to the most semantically similar taxonomy entry.
            phrase_embedding = self.sentence_model.encode(
                phrase,
                convert_to_tensor=True,
                normalize_embeddings=True,
            )
            similarities = util.cos_sim(phrase_embedding, self.taxonomy_embeddings)[0]
            best_idx = int(similarities.argmax())
            taxonomy_score = float(similarities[best_idx])

            topic_name = self.taxonomy[best_idx]
            # Average the two signals: how well the phrase represents the document
            # and how well the phrase matches the taxonomy entry.
            combined_score = (keyphrase_score + taxonomy_score) / 2

            # Deduplicate: if the same taxonomy topic is matched by multiple
            # keyphrases, keep the highest-confidence mapping.
            if topic_name not in seen_topics or combined_score > seen_topics[topic_name]:
                seen_topics[topic_name] = combined_score

        return [
            {"topic_name": name, "confidence": round(score, 4)}
            for name, score in sorted(seen_topics.items(), key=lambda x: x[1], reverse=True)
        ]

    def extract_topics_batch(self, texts: list[str]) -> list[list[dict]]:
        """Extract topics for multiple journal entries."""
        return [self.extract_topics(text) for text in texts]
