from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.sql import func
from src.database import Base


class JournalTopics(Base):
    __tablename__ = "journal_topics"

    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("journals.id", ondelete="CASCADE"), nullable=False)
    topic_name = Column(String(100), nullable=False)
    confidence = Column(Numeric(5, 4), nullable=False)
    ml_model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
