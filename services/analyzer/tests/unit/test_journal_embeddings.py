from unittest.mock import Mock

import pytest
from src.crud import journal_embeddings as journal_embeddings_crud
from src.routers.v1 import journal_embeddings as journal_embeddings_router
from src.routers.v1.journal_embeddings import EncodeRequest


def test_generate_journal_embedding_returns_404_for_missing_journal(monkeypatch):
    embedding_client = Mock()
    embedding_client.model_name = "test-embedding-model"
    db = Mock()

    monkeypatch.setattr(journal_embeddings_router, "get_journal_by_id", Mock(return_value=None))

    with pytest.raises(journal_embeddings_router.HTTPException) as exc_info:
        journal_embeddings_router.generate_journal_embedding(
            journal_id=99999,
            db=db,
            embedding_client=embedding_client,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Journal not found"


def test_generate_journal_embedding_calls_upsert_for_existing_journal(monkeypatch):
    journal = Mock()
    journal.journal_text = "hello world"
    db = Mock()

    embedding_client = Mock()
    embedding_client.model_name = "test-embedding-model"
    embedding_client.encode.return_value = [0.1, 0.2, 0.3]

    upsert_embedding = Mock()

    monkeypatch.setattr(journal_embeddings_router, "get_journal_by_id", Mock(return_value=journal))
    monkeypatch.setattr(journal_embeddings_router, "upsert_embedding", upsert_embedding)

    response = journal_embeddings_router.generate_journal_embedding(
        journal_id=1,
        db=db,
        embedding_client=embedding_client,
    )

    assert response is None
    embedding_client.encode.assert_called_once_with("hello world")
    upsert_embedding.assert_called_once()
    args, kwargs = upsert_embedding.call_args
    assert args[0] is db
    assert args[1] == 1
    assert args[2] == [0.1, 0.2, 0.3]
    assert kwargs["model_version"] == "test-embedding-model"


def test_generate_journal_embedding_returns_500_when_encoding_fails(monkeypatch):
    journal = Mock()
    journal.journal_text = "hello world"
    db = Mock()

    embedding_client = Mock()
    embedding_client.model_name = "test-embedding-model"
    embedding_client.encode.side_effect = RuntimeError("boom")

    monkeypatch.setattr(journal_embeddings_router, "get_journal_by_id", Mock(return_value=journal))

    with pytest.raises(journal_embeddings_router.HTTPException) as exc_info:
        journal_embeddings_router.generate_journal_embedding(
            journal_id=1,
            db=db,
            embedding_client=embedding_client,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Internal server error"


def test_encode_text_returns_embedding():
    embedding_client = Mock()
    embedding_client.encode.return_value = [0.4, 0.5, 0.6]

    response = journal_embeddings_router.encode_text(
        request=EncodeRequest(text="search query"),
        embedding_client=embedding_client,
    )

    assert response == {"embedding": [0.4, 0.5, 0.6], "dimensions": 3}


def test_encode_text_returns_500_when_embedding_fails():
    embedding_client = Mock()
    embedding_client.encode.side_effect = RuntimeError("boom")

    with pytest.raises(journal_embeddings_router.HTTPException) as exc_info:
        journal_embeddings_router.encode_text(
            request=EncodeRequest(text="search query"),
            embedding_client=embedding_client,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Internal server error"


def test_upsert_embedding_commits_with_vector_sql():
    db = Mock()

    journal_embeddings_crud.upsert_embedding(
        db=db,
        journal_id=7,
        embedding=[0.1, 0.2],
        model_version="mini-test",
    )

    db.execute.assert_called_once()
    _, params = db.execute.call_args.args
    assert params == {
        "journal_id": 7,
        "embedding": "[0.1,0.2]",
        "model_version": "mini-test",
    }
    db.commit.assert_called_once()


def test_semantic_search_serializes_results():
    db = Mock()
    row = Mock()
    row.journal_id = 9
    row.journal_text = "hello"
    row.mood_score = 5
    row.created_at = Mock(isoformat=Mock(return_value="2026-04-05T00:00:00+00:00"))
    row.similarity = 0.9123
    db.execute.return_value.fetchall.return_value = [row]

    results = journal_embeddings_crud.semantic_search(
        db=db,
        query_embedding=[0.3, 0.4],
        user_id="user-1",
        limit=5,
    )

    assert results == [
        {
            "journal_id": 9,
            "journal_text": "hello",
            "mood_score": 5,
            "created_at": "2026-04-05T00:00:00+00:00",
            "similarity": 0.9123,
        }
    ]
