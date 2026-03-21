import logging

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingClient:
    """Generates text embeddings using sentence-transformers (all-MiniLM-L6-v2).

    This is the same model used internally by KeyBERT for topic extraction,
    but loaded directly here for explicit embedding generation and search.
    """

    def __init__(self) -> None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        self.model_name = MODEL_NAME
        self.dimensions = 384
        logger.info(f"Embedding model loaded: {MODEL_NAME} ({self.dimensions}d)")

    def encode(self, text: str) -> list[float]:
        """Encode a single text into a 384-dimensional embedding vector."""
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts into embedding vectors."""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
