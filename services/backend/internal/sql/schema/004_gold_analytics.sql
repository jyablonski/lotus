-- +goose Up

CREATE SCHEMA IF NOT EXISTS gold;

-- This table is managed by dbt, but we need the schema here for sqlc to generate the model
CREATE TABLE IF NOT EXISTS gold.user_journal_summary
(
    user_id UUID primary key,
    user_email text,
    user_role text,
    user_timezone text,
    user_created_at timestamp,

    -- All-time metrics
    total_journals integer not null default 0,
    active_days integer not null default 0,
    avg_mood_score numeric,
    min_mood_score integer,
    max_mood_score integer,
    mood_score_stddev numeric,

    -- Sentiment metrics
    positive_entries integer not null default 0,
    negative_entries integer not null default 0,
    neutral_entries integer not null default 0,
    avg_sentiment_score numeric,

    -- Content metrics
    avg_journal_length numeric,

    -- Timestamps
    first_journal_at timestamp,
    last_journal_at timestamp,
    last_modified_at timestamp,

    -- Last 30 days metrics
    total_journals_30d integer not null default 0,
    avg_mood_score_30d numeric,
    min_mood_score_30d integer,
    max_mood_score_30d integer,

    -- Streak and calculated fields
    daily_streak integer not null default 0,
    positive_percentage numeric,
    days_since_last_journal integer,
    days_between_first_and_last_journal integer,
    journals_per_active_day numeric
);


-- +goose Down

DROP TABLE IF EXISTS gold.user_journal_summary;
DROP SCHEMA IF EXISTS gold;
