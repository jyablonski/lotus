import importlib
from unittest.mock import Mock

import pytest
from src.routers.v1 import pact_states as pact_states_module


def _load_pact_module(monkeypatch):
    monkeypatch.setenv("PACT_TESTING", "true")
    return importlib.reload(pact_states_module)


def _endpoint(module):
    assert module.router.routes
    return module.router.routes[0].endpoint


def test_pact_state_setup_creates_journal_when_missing(monkeypatch):
    module = _load_pact_module(monkeypatch)
    endpoint = _endpoint(module)
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = None

    response = endpoint({"state": "a journal entry exists in the analyzer database"}, db=db)

    assert response == {"status": "ok"}
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_pact_state_setup_skips_when_journal_exists(monkeypatch):
    module = _load_pact_module(monkeypatch)
    endpoint = _endpoint(module)
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = Mock()

    response = endpoint({"state": "a journal entry exists in the analyzer database"}, db=db)

    assert response == {"status": "ok"}
    db.add.assert_not_called()


def test_pact_state_teardown_deletes_journal(monkeypatch):
    module = _load_pact_module(monkeypatch)
    endpoint = _endpoint(module)
    db = Mock()
    db.query.return_value.filter.return_value.delete.return_value = 1

    response = endpoint(
        {"state": "a journal entry exists in the analyzer database", "action": "teardown"},
        db=db,
    )

    assert response == {"status": "ok"}
    db.commit.assert_called_once()


def test_pact_state_rolls_back_on_setup_error(monkeypatch):
    module = _load_pact_module(monkeypatch)
    endpoint = _endpoint(module)
    db = Mock()
    db.query.return_value.filter.return_value.first.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        endpoint({"state": "a journal entry exists in the analyzer database"}, db=db)

    db.rollback.assert_called_once()


def test_pact_state_unknown_state_is_noop(monkeypatch):
    module = _load_pact_module(monkeypatch)
    endpoint = _endpoint(module)

    assert endpoint({"state": "unknown state"}, db=Mock()) == {"status": "ok"}
