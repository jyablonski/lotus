"""Provider state handler for Pact contract verification.

This endpoint is only used during contract testing to set up
the appropriate state in the analyzer before verification runs.
"""

import logging
import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.dependencies import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# Only register routes when running contract tests.
# This is also guarded in __init__.py (double-gating ensures the endpoint
# is never exposed even if this module is imported directly).
if os.environ.get("PACT_TESTING", "false").lower() == "true":

    @router.post("/pact/provider-states")
    def handle_provider_state(body: dict, db: Session = Depends(get_db)):
        """Handle provider state setup for Pact verification."""
        state = body.get("state", "")
        action = body.get("action", "setup")

        logger.info("Pact provider state: %s (action=%s)", state, action)

        # Journal ID 123 and user_id must match the consumer contract in
        # services/backend/internal/grpc/contract_test/analyzer_consumer_test.go
        if state == "a journal entry exists in the analyzer database":
            if action == "setup":
                from src.models.journals import Journals

                try:
                    existing = db.query(Journals).filter(Journals.id == 123).first()
                    if not existing:
                        journal = Journals(
                            id=123,
                            user_id="a91b114d-b3de-4fe6-b162-039c9850c06b",
                            journal_text="This is a test journal for contract testing.",
                            mood_score=7,
                        )
                        db.add(journal)
                        db.commit()
                except Exception:
                    db.rollback()
                    raise
            elif action == "teardown":
                from src.models.journals import Journals

                try:
                    db.query(Journals).filter(Journals.id == 123).delete()
                    db.commit()
                except Exception:
                    db.rollback()
                    raise

        return {"status": "ok"}
