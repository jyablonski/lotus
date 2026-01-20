from datetime import timedelta
from feast import FeatureView, Field
from feast.types import Float32, Int64

try:
    from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
        PostgreSQLSource,
    )
except ImportError:
    from feast.data_source import PostgreSQLSource

try:
    from entities import user_entity
except ImportError:
    from feast_repo.entities import user_entity

user_journal_summary_source = PostgreSQLSource(
    name="user_journal_summary",
    query="""
    SELECT
        user_id::text as user_id,
        total_journals,
        active_days,
        avg_mood_score,
        mood_score_stddev,
        positive_entries,
        negative_entries,
        neutral_entries,
        avg_sentiment_score,
        positive_percentage,
        days_since_first_journal,
        journals_per_active_day,
        COALESCE(last_modified_at, last_journal_at, CURRENT_TIMESTAMP) as event_timestamp
    FROM gold.user_journal_summary
    """,
    timestamp_field="event_timestamp",
)

user_journal_summary_fv = FeatureView(
    name="user_journal_summary_features",
    entities=[user_entity],
    ttl=timedelta(days=365),
    source=user_journal_summary_source,
    online=True,
    schema=[
        # REMOVED user_id - it's the entity key, not a feature
        Field(name="total_journals", dtype=Int64),
        Field(name="active_days", dtype=Int64),
        Field(name="avg_mood_score", dtype=Float32),
        Field(name="mood_score_stddev", dtype=Float32),
        Field(name="positive_entries", dtype=Int64),
        Field(name="negative_entries", dtype=Int64),
        Field(name="neutral_entries", dtype=Int64),
        Field(name="avg_sentiment_score", dtype=Float32),
        Field(name="positive_percentage", dtype=Float32),
        Field(name="days_since_first_journal", dtype=Int64),
        Field(name="journals_per_active_day", dtype=Float32),
    ],
)
