-- Schema for backend integration tests (via testcontainers-go).
-- Mirrors docker/db/01-bootstrap.sql but without seed data or unrelated databases.

CREATE SCHEMA source;
CREATE SCHEMA silver;
CREATE SCHEMA gold;
SET search_path TO source;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE source.users
(
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email          VARCHAR NOT NULL UNIQUE,
    password       VARCHAR,
    salt           VARCHAR,
    oauth_provider VARCHAR,
    role           VARCHAR NOT NULL DEFAULT 'Consumer',
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    timezone       VARCHAR NOT NULL DEFAULT 'UTC'
);

CREATE TABLE source.user_game_balances (
    id          SERIAL PRIMARY KEY,
    user_id     UUID NOT NULL UNIQUE REFERENCES source.users(id) ON DELETE CASCADE,
    balance     INTEGER NOT NULL DEFAULT 100,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE source.user_game_bets (
    id          SERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES source.users(id) ON DELETE CASCADE,
    zone        VARCHAR(10) NOT NULL,
    amount      INTEGER NOT NULL,
    roll_result INTEGER NOT NULL,
    payout      INTEGER NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_game_bets_user_created ON source.user_game_bets (user_id, created_at DESC);

CREATE TABLE source.journals
(
    id           SERIAL PRIMARY KEY,
    user_id      UUID NOT NULL,
    journal_text TEXT NOT NULL,
    mood_score   INTEGER,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_journals_user_id_created_at ON source.journals (user_id, created_at DESC);

CREATE TABLE source.journal_details (
    journal_id      INTEGER PRIMARY KEY REFERENCES source.journals(id) ON DELETE CASCADE,
    sentiment_score FLOAT,
    mood_label      TEXT,
    keywords        TEXT[],
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE source.journal_topics (
    id               SERIAL PRIMARY KEY,
    journal_id       INTEGER REFERENCES source.journals(id) ON DELETE CASCADE,
    topic_name       VARCHAR(100) NOT NULL,
    confidence       DECIMAL(5,4) NOT NULL,
    ml_model_version VARCHAR(50) NOT NULL,
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_journal_topics_journal_id ON source.journal_topics (journal_id);
CREATE INDEX idx_journal_topics_topic_name ON source.journal_topics (topic_name);

CREATE TABLE source.journal_sentiments (
    id               SERIAL PRIMARY KEY,
    journal_id       INTEGER REFERENCES source.journals(id) ON DELETE CASCADE,
    sentiment        VARCHAR(20) NOT NULL CHECK (sentiment IN ('positive', 'negative', 'neutral', 'uncertain')),
    confidence       DECIMAL(5,4) NOT NULL,
    confidence_level VARCHAR(10) NOT NULL CHECK (confidence_level IN ('high', 'medium', 'low')),
    is_reliable      BOOLEAN NOT NULL DEFAULT TRUE,
    ml_model_version VARCHAR(50) NOT NULL,
    created_at       TIMESTAMP DEFAULT NOW(),
    all_scores       JSONB,
    UNIQUE (journal_id, ml_model_version)
);

CREATE TABLE source.runtime_config
(
    id          SERIAL PRIMARY KEY,
    key         VARCHAR(255) NOT NULL UNIQUE,
    value       JSONB NOT NULL DEFAULT '{}',
    service     VARCHAR(50) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Truncate all integration test tables in FK-safe order.
CREATE OR REPLACE FUNCTION source.truncate_integration_tables()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  TRUNCATE source.journal_sentiments, source.journal_topics, source.journal_details,
           source.journals, source.user_game_bets, source.user_game_balances, source.users
  RESTART IDENTITY CASCADE;
END;
$$;
