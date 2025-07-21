from collections.abc import Generator

from sqlalchemy.orm import Session

from src.database import SessionLocal


def get_db() -> Generator[Session]:
    """FastAPI Dependency for Database Operations

    Used in Endpoints that require Database ops

    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
