import logging

from sqlalchemy.orm import Session
from src.models.journals import Journals


def get_journal_by_id(db: Session, journal_id: int) -> Journals | None:
    """Get a journal entry by ID"""
    logging.info(f"Querying for journal with ID: {journal_id}")

    query = db.query(Journals).filter(Journals.id == journal_id)
    logging.info(f"SQL Query: {query}")

    result = query.first()
    logging.info(f"Query result: {result}")

    return result


def get_journal_by_id_and_user(db: Session, journal_id: int, user_id: str) -> Journals | None:
    """Get a journal entry by ID and user ID (for security)"""
    return db.query(Journals).filter(Journals.id == journal_id, Journals.user_id == user_id).first()


def get_journals_by_user(
    db: Session, user_id: str, skip: int = 0, limit: int = 100
) -> list[Journals]:
    """Get all journal entries for a user"""
    return db.query(Journals).filter(Journals.user_id == user_id).offset(skip).limit(limit).all()


def get_all_journals(db: Session, skip: int = 0, limit: int = 100) -> list[Journals]:
    """Get all journal entries (admin use)"""
    return db.query(Journals).offset(skip).limit(limit).all()
