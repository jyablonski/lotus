from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Column,
    Float,
    Integer,
    Text,
    func,
)
from src.database import Base


class JournalDetails(Base):
    __tablename__ = "journal_details"

    journal_id = Column(
        Integer,
        primary_key=True,  # Removed ForeignKey constraint
    )
    sentiment_score = Column(Float, nullable=True)
    mood_label = Column(Text, nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    modified_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
