from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.sql import func
from src.database import Base


class JournalSentiments(Base):
    __tablename__ = "journal_sentiments"

    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(
        Integer,
        ForeignKey("journals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sentiment = Column(String(20), nullable=False, index=True)
    confidence = Column(Numeric(5, 4), nullable=False)
    confidence_level = Column(String(10), nullable=False, index=True)
    is_reliable = Column(Boolean, nullable=False, default=True, index=True)
    ml_model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    all_scores = Column(JSON, nullable=True)  # Store individual sentiment probabilities

    @property
    def sentiment_summary(self):
        """Helper property for API responses"""
        return {
            "sentiment": self.sentiment,
            "confidence": float(self.confidence),
            "confidence_level": self.confidence_level,
            "is_reliable": self.is_reliable,
            "model_version": self.ml_model_version,
        }

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "journal_id": self.journal_id,
            "sentiment": self.sentiment,
            "confidence": float(self.confidence),
            "confidence_level": self.confidence_level,
            "is_reliable": self.is_reliable,
            "ml_model_version": self.ml_model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "all_scores": self.all_scores,
        }
