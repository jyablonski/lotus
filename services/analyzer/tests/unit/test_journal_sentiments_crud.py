from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest
from src.crud import journal_sentiments as crud
from src.models.journal_sentiments import JournalSentiments


def test_create_or_update_sentiment_returns_existing_when_not_forced():
    existing = Mock()
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = existing

    result = crud.create_or_update_sentiment(
        db=db,
        journal_id=1,
        sentiment_data={
            "sentiment": "positive",
            "confidence": 0.9,
            "confidence_level": "high",
            "is_reliable": True,
            "ml_model_version": "v1",
        },
        force_update=False,
    )

    assert result is existing
    db.commit.assert_not_called()


def test_create_or_update_sentiment_updates_existing_when_forced():
    existing = Mock()
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = existing

    result = crud.create_or_update_sentiment(
        db=db,
        journal_id=1,
        sentiment_data={
            "sentiment": "negative",
            "confidence": 0.2,
            "confidence_level": "low",
            "is_reliable": False,
            "ml_model_version": "v1",
            "all_scores": {"negative": 0.2},
        },
        force_update=True,
    )

    assert result is existing
    assert existing.sentiment == "negative"
    assert existing.is_reliable is False
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(existing)


def test_create_or_update_sentiment_creates_new_record():
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = crud.create_or_update_sentiment(
        db=db,
        journal_id=3,
        sentiment_data={
            "sentiment": "positive",
            "confidence": 0.95,
            "confidence_level": "high",
            "is_reliable": True,
            "ml_model_version": "v2",
            "all_scores": {"positive": 0.95},
        },
    )

    assert isinstance(result, JournalSentiments)
    assert result.journal_id == 3
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_create_or_update_sentiment_rolls_back_on_error():
    db = Mock()

    with pytest.raises(KeyError):
        crud.create_or_update_sentiment(db=db, journal_id=1, sentiment_data={})

    db.rollback.assert_called_once()


def test_get_sentiment_by_journal_id_returns_latest_record():
    record = Mock()
    order_query = Mock()
    order_query.first.return_value = record
    query = Mock()
    query.filter.return_value = query
    query.order_by.return_value = order_query
    db = Mock()
    db.query.return_value = query

    result = crud.get_sentiment_by_journal_id(db=db, journal_id=1, model_version="v1")

    assert result is record


def test_get_sentiments_by_journal_ids_returns_all_records():
    sentiments = [Mock(), Mock()]
    order_query = Mock()
    order_query.all.return_value = sentiments
    query = Mock()
    query.filter.return_value = query
    query.order_by.return_value = order_query
    db = Mock()
    db.query.return_value = query

    result = crud.get_sentiments_by_journal_ids(db=db, journal_ids=[1, 2], reliable_only=False)

    assert result == sentiments


def test_get_sentiment_trends_aggregates_rows():
    now = datetime.now()
    db = Mock()
    aggregate_query = Mock()
    aggregate_query.filter.return_value = aggregate_query
    aggregate_query.group_by.return_value = aggregate_query
    aggregate_query.order_by.return_value = aggregate_query
    aggregate_query.all.return_value = [
        (now, "positive", 2, 0.8),
        (now, "negative", 1, 0.4),
    ]
    db.query.side_effect = [
        Mock(filter=Mock(return_value=Mock(filter=Mock(return_value=Mock())))),
        aggregate_query,
    ]

    result = crud.get_sentiment_trends(db=db, days_back=7, group_by="day")

    assert len(result) == 1
    assert result[0]["total_entries"] == 3
    assert result[0]["dominant_sentiment"] == "positive"


def test_get_sentiment_stats_returns_empty_defaults():
    db = Mock()
    db.query.return_value.all.return_value = []

    result = crud.get_sentiment_stats(db=db)

    assert result["total_analyzed"] == 0
    assert result["latest_model_version"] is None


def test_get_sentiment_stats_returns_aggregated_values():
    s1 = Mock(
        is_reliable=True,
        sentiment="positive",
        confidence=Decimal("0.9"),
        created_at=datetime.now() - timedelta(days=1),
        ml_model_version="v1",
    )
    s2 = Mock(
        is_reliable=False,
        sentiment="negative",
        confidence=Decimal("0.3"),
        created_at=datetime.now(),
        ml_model_version="v2",
    )
    db = Mock()
    db.query.return_value.all.return_value = [s1, s2]

    result = crud.get_sentiment_stats(db=db)

    assert result["total_analyzed"] == 2
    assert result["reliable_count"] == 1
    assert result["latest_model_version"] == "v2"


def test_get_recent_sentiments_returns_limited_results():
    sentiments = [Mock()]
    limited_query = Mock()
    limited_query.all.return_value = sentiments
    ordered_query = Mock()
    ordered_query.limit.return_value = limited_query
    query = Mock()
    query.filter.return_value = query
    query.order_by.return_value = ordered_query
    db = Mock()
    db.query.return_value = query

    result = crud.get_recent_sentiments(db=db, limit=1)

    assert result == sentiments


def test_bulk_create_sentiments_creates_and_refreshes_records():
    db = Mock()
    payload = [
        (
            1,
            {
                "sentiment": "positive",
                "confidence": 0.8,
                "confidence_level": "high",
                "is_reliable": True,
                "ml_model_version": "v1",
            },
        )
    ]

    result = crud.bulk_create_sentiments(db=db, sentiment_data_list=payload)

    assert len(result) == 1
    assert isinstance(result[0], JournalSentiments)
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_delete_sentiment_returns_deleted_count():
    query = Mock()
    query.filter.return_value = query
    query.delete.return_value = 2
    db = Mock()
    db.query.return_value = query

    result = crud.delete_sentiment(db=db, journal_id=1, model_version=None)

    assert result == 2
    db.commit.assert_called_once()
