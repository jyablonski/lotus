#!/usr/bin/env python3
"""One-time backfill script to generate embeddings for all existing journals.

Calls the analyzer's embedding endpoint for each journal that doesn't already
have an embedding. Run manually after deploying the pgvector migration:

    python scripts/backfill_embeddings.py

Environment variables:
    ANALYZER_URL      Base URL of the analyzer service (default: http://localhost:8083)
    ANALYZER_API_KEY  API key for the analyzer service (required)
    DATABASE_URL      PostgreSQL connection string (default: postgresql://postgres:postgres@localhost:5432/postgres)
    BATCH_DELAY       Seconds to wait between requests (default: 0.1)
"""

import os
import sys
import time

import httpx
import psycopg2

ANALYZER_URL = os.environ.get("ANALYZER_URL", "http://localhost:8083")
ANALYZER_API_KEY = os.environ.get("ANALYZER_API_KEY", "")
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres",
)
BATCH_DELAY = float(os.environ.get("BATCH_DELAY", "0.1"))


def main() -> None:
    if not ANALYZER_API_KEY:
        print("ERROR: ANALYZER_API_KEY environment variable is required.")
        sys.exit(1)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SET search_path TO source")

    # Find journals that don't yet have embeddings
    cur.execute("""
        SELECT j.id
        FROM journals j
        LEFT JOIN journal_embeddings je ON j.id = je.journal_id
        WHERE je.id IS NULL
        ORDER BY j.id
    """)
    journal_ids = [row[0] for row in cur.fetchall()]

    if not journal_ids:
        print("All journals already have embeddings. Nothing to do.")
        cur.close()
        conn.close()
        return

    print(f"Found {len(journal_ids)} journals without embeddings. Starting backfill...")

    success = 0
    failed = 0

    headers = {"Authorization": f"Bearer {ANALYZER_API_KEY}"}

    with httpx.Client(timeout=30.0, headers=headers) as client:
        for i, journal_id in enumerate(journal_ids, 1):
            try:
                resp = client.post(f"{ANALYZER_URL}/v1/journals/{journal_id}/embeddings")
                resp.raise_for_status()
                success += 1
            except Exception as e:
                print(f"  FAILED journal {journal_id}: {e}")
                failed += 1

            if i % 50 == 0:
                print(f"  Progress: {i}/{len(journal_ids)} (success={success}, failed={failed})")

            time.sleep(BATCH_DELAY)

    print(
        f"\nBackfill complete: {success} succeeded, {failed} failed out of {len(journal_ids)} total."
    )

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
