from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from src.database import Base


class JournalEmbeddings(Base):
    __tablename__ = "journal_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("journals.id", ondelete="CASCADE"), nullable=False)
    embedding = Column(Text, nullable=False)  # stored as vector(384) via pgvector
    model_version = Column(String(50), nullable=False, default="all-MiniLM-L6-v2")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
