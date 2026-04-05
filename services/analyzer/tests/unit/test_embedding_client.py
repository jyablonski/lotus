from unittest.mock import Mock

from src.clients import embedding_client as embedding_module


def test_embedding_client_initializes_model(monkeypatch):
    transformer = Mock()
    constructor = Mock(return_value=transformer)
    monkeypatch.setattr(embedding_module, "SentenceTransformer", constructor)

    client = embedding_module.EmbeddingClient()

    constructor.assert_called_once_with(embedding_module.MODEL_NAME)
    assert client.model is transformer
    assert client.model_name == embedding_module.MODEL_NAME
    assert client.dimensions == 384


def test_embedding_client_encode_returns_list(monkeypatch):
    encoded = Mock()
    encoded.tolist.return_value = [0.1, 0.2]
    transformer = Mock()
    transformer.encode.return_value = encoded
    monkeypatch.setattr(embedding_module, "SentenceTransformer", Mock(return_value=transformer))

    client = embedding_module.EmbeddingClient()

    assert client.encode("hello") == [0.1, 0.2]
    transformer.encode.assert_called_once_with("hello", normalize_embeddings=True)


def test_embedding_client_encode_batch_returns_list(monkeypatch):
    encoded = Mock()
    encoded.tolist.return_value = [[0.1, 0.2], [0.3, 0.4]]
    transformer = Mock()
    transformer.encode.return_value = encoded
    monkeypatch.setattr(embedding_module, "SentenceTransformer", Mock(return_value=transformer))

    client = embedding_module.EmbeddingClient()

    assert client.encode_batch(["a", "b"]) == [[0.1, 0.2], [0.3, 0.4]]
    transformer.encode.assert_called_once_with(["a", "b"], normalize_embeddings=True)
