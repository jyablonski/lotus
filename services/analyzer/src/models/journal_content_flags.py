from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from src.database import Base


class JournalContentFlags(Base):
    __tablename__ = "journal_content_flags"

    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("journals.id", ondelete="CASCADE"), nullable=False)
    flag_type = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False)
    matched_terms = Column(ARRAY(Text), nullable=False)
    analysis_summary = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
