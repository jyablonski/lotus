import logging

from sqlalchemy.orm import Session
from src.content_safety.schemas import ContentFlagAnalysis
from src.models.journal_content_flags import JournalContentFlags

logger = logging.getLogger(__name__)


def create_journal_content_flag(
    db: Session, journal_id: int, analysis: ContentFlagAnalysis
) -> JournalContentFlags:
    record = JournalContentFlags(
        journal_id=journal_id,
        flag_type=analysis.flag_type,
        severity=analysis.severity,
        matched_terms=analysis.matched_terms,
        analysis_summary=analysis.analysis_summary,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.error(
        "journal_content_flag_written journal_id=%s flag_type=%s severity=%s matched_terms=%s",
        journal_id,
        analysis.flag_type,
        analysis.severity,
        analysis.matched_terms,
        extra={
            "journal_id": journal_id,
            "flag_type": analysis.flag_type,
            "severity": analysis.severity,
            "matched_terms": analysis.matched_terms,
        },
    )

    return record
