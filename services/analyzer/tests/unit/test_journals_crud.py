from unittest.mock import Mock

from src.crud import journals as crud


def test_get_journal_by_id_returns_first():
    expected = Mock()
    query = Mock()
    query.first.return_value = expected
    filtered = Mock(return_value=query)
    db = Mock()
    db.query.return_value.filter = filtered

    assert crud.get_journal_by_id(db=db, journal_id=1) is expected


def test_get_journal_by_id_and_user_filters_both_fields():
    expected = Mock()
    query = Mock()
    query.first.return_value = expected
    db = Mock()
    db.query.return_value.filter.return_value = query

    assert crud.get_journal_by_id_and_user(db=db, journal_id=1, user_id="user-1") is expected


def test_get_journals_by_user_applies_offset_and_limit():
    expected = [Mock()]
    limited = Mock()
    limited.all.return_value = expected
    offset = Mock()
    offset.limit.return_value = limited
    filtered = Mock()
    filtered.offset.return_value = offset
    db = Mock()
    db.query.return_value.filter.return_value = filtered

    assert crud.get_journals_by_user(db=db, user_id="user-1", skip=5, limit=10) == expected


def test_get_all_journals_applies_offset_and_limit():
    expected = [Mock()]
    limited = Mock()
    limited.all.return_value = expected
    offset = Mock()
    offset.limit.return_value = limited
    db = Mock()
    db.query.return_value.offset.return_value = offset

    assert crud.get_all_journals(db=db, skip=1, limit=2) == expected
