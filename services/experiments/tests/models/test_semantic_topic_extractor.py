"""Unit tests for SemanticTopicExtractor.

These tests use a lightweight mock sentence-transformer to avoid pulling the full
~80 MB model during unit test runs. Integration tests (requiring the real model
or a running MLflow) are marked with @pytest.mark.integration.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from src.models.semantic_topic_extractor import (
    JOURNAL_TOPIC_TAXONOMY,
    SemanticTopicExtractor,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_mock_extractor(taxonomy: list[str] | None = None) -> SemanticTopicExtractor:
    """Return a SemanticTopicExtractor with mocked sentence-transformer and KeyBERT.

    Mocked behaviour:
    - SentenceTransformer.encode returns fixed unit vectors (one per input).
    - KeyBERT.extract_keywords returns a hard-coded keyphrase list.
    - Cosine similarity always maps to the first taxonomy entry for simplicity.
    """
    tax = taxonomy or JOURNAL_TOPIC_TAXONOMY[:5]

    with (
        patch("src.models.semantic_topic_extractor.SentenceTransformer") as MockST,
        patch("src.models.semantic_topic_extractor.KeyBERT") as MockKB,
    ):
        mock_st_instance = MagicMock()
        # encode returns a numpy-compatible tensor; shape matches taxonomy or single phrase
        mock_st_instance.encode.side_effect = lambda texts, **kwargs: (
            np.ones((len(texts), 4), dtype="float32")
            if isinstance(texts, list)
            else np.ones((1, 4), dtype="float32")
        )
        MockST.return_value = mock_st_instance

        mock_kb_instance = MagicMock()
        MockKB.return_value = mock_kb_instance

        extractor = SemanticTopicExtractor(taxonomy=tax)

    # Replace taxonomy_embeddings with a real numpy array so cosine sim works.
    extractor.taxonomy_embeddings = np.ones((len(tax), 4), dtype="float32")

    return extractor


# ---------------------------------------------------------------------------
# Taxonomy tests
# ---------------------------------------------------------------------------


class TestTaxonomy:
    def test_default_taxonomy_not_empty(self):
        assert len(JOURNAL_TOPIC_TAXONOMY) > 0

    def test_all_taxonomy_entries_are_strings(self):
        assert all(isinstance(t, str) and t for t in JOURNAL_TOPIC_TAXONOMY)

    def test_no_duplicate_taxonomy_entries(self):
        assert len(JOURNAL_TOPIC_TAXONOMY) == len(set(JOURNAL_TOPIC_TAXONOMY))


# ---------------------------------------------------------------------------
# Initialisation tests
# ---------------------------------------------------------------------------


class TestSemanticTopicExtractorInit:
    def test_custom_taxonomy_stored(self):
        extractor = _make_mock_extractor(taxonomy=["a", "b", "c"])
        assert extractor.taxonomy == ["a", "b", "c"]

    def test_default_taxonomy_used_when_none(self):
        extractor = _make_mock_extractor(taxonomy=None)
        assert extractor.taxonomy == JOURNAL_TOPIC_TAXONOMY[:5]

    def test_default_ngram_range(self):
        extractor = _make_mock_extractor()
        assert extractor.keyphrase_ngram_range == (1, 3)

    def test_default_min_confidence(self):
        extractor = _make_mock_extractor()
        assert extractor.min_confidence == 0.25


# ---------------------------------------------------------------------------
# extract_topics output format tests
# ---------------------------------------------------------------------------


class TestExtractTopicsFormat:
    def _extractor_with_keyphrases(
        self, keyphrases: list[tuple[str, float]]
    ) -> SemanticTopicExtractor:
        extractor = _make_mock_extractor()
        extractor.kw_model.extract_keywords.return_value = keyphrases
        return extractor

    def test_returns_list(self):
        extractor = self._extractor_with_keyphrases([("work stress", 0.80)])
        result = extractor.extract_topics("Some text about work")
        assert isinstance(result, list)

    def test_each_topic_has_required_keys(self):
        extractor = self._extractor_with_keyphrases([("work stress", 0.80)])
        result = extractor.extract_topics("Some text about work")
        for topic in result:
            assert "topic_name" in topic
            assert "confidence" in topic

    def test_confidence_rounded_to_4_decimals(self):
        extractor = self._extractor_with_keyphrases([("work stress", 0.80)])
        result = extractor.extract_topics("Some text about work")
        for topic in result:
            # confidence should have at most 4 decimal places
            assert round(topic["confidence"], 4) == topic["confidence"]

    def test_sorted_by_descending_confidence(self):
        extractor = _make_mock_extractor(taxonomy=["topic a", "topic b", "topic c"])
        extractor.taxonomy_embeddings = np.eye(3, dtype="float32")

        # Simulate three distinct keyphrases mapping to different taxonomy entries
        def mock_encode(text, **kwargs):
            phrase_map = {
                "first phrase": np.array([[1.0, 0.0, 0.0]], dtype="float32"),
                "second phrase": np.array([[0.0, 1.0, 0.0]], dtype="float32"),
                "third phrase": np.array([[0.0, 0.0, 1.0]], dtype="float32"),
            }
            return phrase_map.get(text, np.zeros((1, 3), dtype="float32"))

        extractor.sentence_model.encode = mock_encode
        extractor.kw_model.extract_keywords.return_value = [
            ("first phrase", 0.90),
            ("second phrase", 0.50),
            ("third phrase", 0.70),
        ]

        result = extractor.extract_topics("x " * 30)
        confidences = [t["confidence"] for t in result]
        assert confidences == sorted(confidences, reverse=True)

    def test_empty_text_returns_list(self):
        extractor = _make_mock_extractor()
        extractor.kw_model.extract_keywords.return_value = []
        result = extractor.extract_topics("")
        assert isinstance(result, list)

    def test_no_keyphrases_returns_empty(self):
        extractor = _make_mock_extractor()
        extractor.kw_model.extract_keywords.return_value = []
        result = extractor.extract_topics("hello")
        assert result == []

    def test_low_confidence_keyphrases_filtered(self):
        extractor = _make_mock_extractor()
        # All below min_confidence of 0.25
        extractor.kw_model.extract_keywords.return_value = [
            ("low score phrase", 0.10),
            ("another low one", 0.20),
        ]
        result = extractor.extract_topics("Some text")
        assert result == []


# ---------------------------------------------------------------------------
# Adaptive keyphrase count tests
# ---------------------------------------------------------------------------


class TestAdaptiveKeyphraseCount:
    def _extractor_tracking_top_n(self) -> tuple[SemanticTopicExtractor, list[int]]:
        extractor = _make_mock_extractor()
        captured_top_n: list[int] = []

        def mock_extract(text, **kwargs):
            captured_top_n.append(kwargs.get("top_n", -1))
            return []

        extractor.kw_model.extract_keywords.side_effect = mock_extract
        return extractor, captured_top_n

    def test_short_entry_uses_top_n_2(self):
        extractor, captured = self._extractor_tracking_top_n()
        # < 20 words
        extractor.extract_topics("Short entry text")
        assert captured[0] == 2

    def test_medium_entry_uses_top_n_4(self):
        extractor, captured = self._extractor_tracking_top_n()
        # 20-49 words
        text = " ".join(["word"] * 30)
        extractor.extract_topics(text)
        assert captured[0] == 4

    def test_long_entry_uses_top_n_6(self):
        extractor, captured = self._extractor_tracking_top_n()
        # >= 50 words
        text = " ".join(["word"] * 60)
        extractor.extract_topics(text)
        assert captured[0] == 6


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_duplicate_taxonomy_mappings_deduplicated(self):
        """Two keyphrases mapping to the same taxonomy entry should yield one topic."""
        extractor = _make_mock_extractor(taxonomy=["work and career"])
        # Both keyphrases map to the only taxonomy entry (index 0).
        extractor.taxonomy_embeddings = np.ones((1, 4), dtype="float32")
        extractor.sentence_model.encode = lambda text, **kwargs: np.ones((1, 4), dtype="float32")
        extractor.kw_model.extract_keywords.return_value = [
            ("work deadline", 0.85),
            ("office project", 0.70),
        ]

        result = extractor.extract_topics("x " * 30)
        # Should be deduplicated to a single topic
        assert len(result) == 1
        assert result[0]["topic_name"] == "work and career"

    def test_duplicate_keeps_highest_confidence(self):
        extractor = _make_mock_extractor(taxonomy=["work and career"])
        extractor.taxonomy_embeddings = np.ones((1, 4), dtype="float32")
        extractor.sentence_model.encode = lambda text, **kwargs: np.ones((1, 4), dtype="float32")
        extractor.kw_model.extract_keywords.return_value = [
            ("work deadline", 0.90),  # higher keyphrase score
            ("office project", 0.40),  # lower
        ]

        result = extractor.extract_topics("x " * 30)
        # Combined score for "work deadline": (0.90 + 1.0) / 2 = 0.95
        # Combined score for "office project": (0.40 + 1.0) / 2 = 0.70
        # Should keep the higher one
        assert result[0]["confidence"] > 0.70


# ---------------------------------------------------------------------------
# Batch extraction tests
# ---------------------------------------------------------------------------


class TestBatchExtraction:
    def test_extract_topics_batch_returns_list_of_lists(self):
        extractor = _make_mock_extractor()
        extractor.kw_model.extract_keywords.return_value = [("work", 0.80)]
        extractor.sentence_model.encode = lambda text, **kwargs: np.ones(
            (1, len(extractor.taxonomy)), dtype="float32"
        )
        result = extractor.extract_topics_batch(["Entry one", "Entry two"])
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(r, list) for r in result)

    def test_batch_length_matches_input(self):
        extractor = _make_mock_extractor()
        extractor.kw_model.extract_keywords.return_value = []
        texts = ["a", "b", "c", "d", "e"]
        result = extractor.extract_topics_batch(texts)
        assert len(result) == len(texts)


# ---------------------------------------------------------------------------
# Integration test (skipped by default — requires real model)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.slow
class TestSemanticTopicExtractorIntegration:
    """Runs with the actual sentence-transformer model. Requires keybert + sentence-transformers."""

    @pytest.fixture(scope="class")
    def extractor(self):
        return SemanticTopicExtractor()

    def test_work_entry_produces_topics(self, extractor):
        text = (
            "Had three back-to-back meetings today and still couldn't finish the "
            "report my manager needs by Friday. Completely overwhelmed."
        )
        topics = extractor.extract_topics(text)
        assert len(topics) > 0
        # Check both topic_name (domain) and subtopic_name — valid models may
        # classify "overwhelmed" under "wellbeing" with subtopic
        # "stress and feeling overwhelmed" rather than "work".
        assert any(
            any(
                kw in (t["topic_name"] + " " + (t.get("subtopic_name") or ""))
                for kw in ("work", "stress", "overwhelm")
            )
            for t in topics
        )

    def test_confidence_in_valid_range(self, extractor):
        text = "Feeling anxious about the big presentation tomorrow."
        topics = extractor.extract_topics(text)
        for topic in topics:
            assert 0.0 <= topic["confidence"] <= 1.0

    def test_short_entry_max_2_topics(self, extractor):
        text = "Tired and sad."
        topics = extractor.extract_topics(text)
        assert len(topics) <= 2

    def test_batch_matches_individual(self, extractor):
        texts = [
            "Great workout today, feeling strong.",
            "Missing my family so much right now.",
        ]
        batch_results = extractor.extract_topics_batch(texts)
        individual_results = [extractor.extract_topics(t) for t in texts]
        assert batch_results == individual_results
