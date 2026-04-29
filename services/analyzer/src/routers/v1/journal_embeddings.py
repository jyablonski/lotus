import logging
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from opentelemetry import trace
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.clients.embedding_client import EmbeddingClient
from src.crud.journal_embeddings import upsert_embedding
from src.crud.journals import get_journal_by_id
from src.dependencies import get_db, get_embedding_client

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
router = APIRouter()


class EncodeRequest(BaseModel):
    text: str


@router.post("/journals/{journal_id}/embeddings", status_code=status.HTTP_204_NO_CONTENT)
def generate_journal_embedding(
    journal_id: int,
    db: Session = Depends(get_db),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
):
    """Generate and store an embedding for a journal entry."""
    journal = get_journal_by_id(db, journal_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")

    try:
        with tracer.start_as_current_span("embeddings.generate") as span:
            span.set_attribute("journal.id", journal_id)
            span.set_attribute("model.name", embedding_client.model_name)

            journal_text = cast("str", journal.journal_text)
            embedding = embedding_client.encode(journal_text)
            span.set_attribute("embedding.dimensions", len(embedding))

        upsert_embedding(db, journal_id, embedding, model_version=embedding_client.model_name)
        logger.info(f"Generated embedding for journal {journal_id}")

    except Exception as e:
        logger.error(f"Error generating embedding for journal {journal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.post("/embeddings/encode")
def encode_text(
    request: EncodeRequest,
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
):
    """Encode arbitrary text into an embedding vector. Used by the Go backend
    to embed search queries before running pgvector similarity search."""
    try:
        with tracer.start_as_current_span("embeddings.encode") as span:
            span.set_attribute("text.length", len(request.text))
            embedding = embedding_client.encode(request.text)
            span.set_attribute("embedding.dimensions", len(embedding))

        return {"embedding": embedding, "dimensions": len(embedding)}

    except Exception as e:
        logger.error(f"Error encoding text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from None
