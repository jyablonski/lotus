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


# Only register this router when running contract tests
if os.environ.get("PACT_TESTING", "false").lower() == "true":

    @router.post("/pact/provider-states")
    def handle_provider_state(body: dict, db: Session = Depends(get_db)):
        """Handle provider state setup for Pact verification."""
        state = body.get("state", "")
        action = body.get("action", "setup")

        logger.info(f"Pact provider state: {state} (action={action})")

        if state == "a journal entry exists in the analyzer database":
            if action == "setup":
                # Insert a test journal if it doesn't exist
                from src.models.journals import Journals

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
            elif action == "teardown":
                from src.models.journals import Journals

                db.query(Journals).filter(Journals.id == 123).delete()
                db.commit()

        return {"status": "ok"}
