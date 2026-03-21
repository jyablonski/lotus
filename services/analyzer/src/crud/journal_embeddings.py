import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_VERSION = "all-MiniLM-L6-v2"


def upsert_embedding(
    db: Session,
    journal_id: int,
    embedding: list[float],
    model_version: str = EMBEDDING_MODEL_VERSION,
) -> None:
    """Insert or update the embedding for a journal entry.

    Uses raw SQL because SQLAlchemy doesn't natively handle pgvector types.
    """
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
    db.execute(
        text("""
            INSERT INTO journal_embeddings (journal_id, embedding, model_version)
            VALUES (:journal_id, CAST(:embedding AS public.vector), :model_version)
            ON CONFLICT (journal_id, model_version)
            DO UPDATE SET embedding = EXCLUDED.embedding
        """),
        {"journal_id": journal_id, "embedding": embedding_str, "model_version": model_version},
    )
    db.commit()
    logger.info(f"Upserted embedding for journal {journal_id} (model={model_version})")


def semantic_search(
    db: Session, query_embedding: list[float], user_id: str, limit: int = 20
) -> list[dict]:
    """Search journals by cosine similarity using pgvector.

    Returns list of dicts with journal_id and similarity score (1 - cosine distance).
    """
    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
    rows = db.execute(
        text("""
            SELECT j.id AS journal_id,
                   j.journal_text,
                   j.mood_score,
                   j.created_at,
                   1 - (je.embedding <=> :embedding::public.vector) AS similarity
            FROM journals j
            JOIN journal_embeddings je ON j.id = je.journal_id
            WHERE j.user_id = :user_id
            ORDER BY je.embedding <=> :embedding::public.vector ASC
            LIMIT :limit
        """),
        {"embedding": embedding_str, "user_id": user_id, "limit": limit},
    ).fetchall()

    return [
        {
            "journal_id": row.journal_id,
            "journal_text": row.journal_text,
            "mood_score": row.mood_score,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]
