-- +goose Up

CREATE TABLE IF NOT EXISTS source.journal_sentiments (
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

-- +goose Down

DROP TABLE IF EXISTS source.journal_sentiments;
