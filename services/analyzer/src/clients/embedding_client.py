import logging
import os

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
        local_files_only = os.getenv("HF_HUB_OFFLINE") == "1"
        self.model = SentenceTransformer(MODEL_NAME, local_files_only=local_files_only)
        self.model_name = MODEL_NAME
        self.dimensions = 384
        logger.info(f"Embedding model loaded: {MODEL_NAME} ({self.dimensions}d)")

    def is_ready(self) -> bool:
        """Check if the embedding model is loaded and ready to use."""
        return self.model is not None

    def get_model_info(self) -> dict:
        """Get current embedding model information."""
        if not self.is_ready():
            return {"status": "not_loaded"}
        return {
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "status": "loaded",
        }

    def encode(self, text: str) -> list[float]:
        """Encode a single text into a 384-dimensional embedding vector."""
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts into embedding vectors."""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
