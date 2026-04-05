from unittest.mock import Mock

import pytest
from src.crud import journal_topics as crud
from src.models.journal_topics import JournalTopics


def test_create_or_update_topics_normalizes_values():
    db = Mock()
    query = Mock()
    query.filter.return_value = query
    db.query.return_value = query

    records = crud.create_or_update_topics(
        db=db,
        journal_id=1,
        topics=[
            {
                "topic_name": " Work ",
                "subtopic_name": " Meetings ",
                "confidence": 0.8,
                "ml_model_version": "v1",
            }
        ],
    )

    assert len(records) == 1
    assert isinstance(records[0], JournalTopics)
    assert records[0].topic_name == "work"
    assert records[0].subtopic_name == "meetings"
    db.commit.assert_called_once()


def test_create_or_update_topics_rolls_back_on_error():
    db = Mock()
    query = Mock()
    query.filter.return_value = query
    db.query.return_value = query
    db.add.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        crud.create_or_update_topics(
            db=db,
            journal_id=1,
            topics=[{"topic_name": "work", "confidence": 0.8, "ml_model_version": "v1"}],
        )

    db.rollback.assert_called_once()


def test_get_topics_by_journal_id_returns_records():
    expected = [Mock()]
    query = Mock()
    query.filter.return_value.all.return_value = expected
    db = Mock()
    db.query.return_value = query

    assert crud.get_topics_by_journal_id(db=db, journal_id=1) == expected


def test_get_topics_by_model_version_returns_records():
    expected = [Mock()]
    query = Mock()
    query.filter.return_value.all.return_value = expected
    db = Mock()
    db.query.return_value = query

    assert crud.get_topics_by_model_version(db=db, model_version="v1") == expected
