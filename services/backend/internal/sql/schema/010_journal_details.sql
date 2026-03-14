-- +goose Up

CREATE TABLE IF NOT EXISTS source.journal_details (
    journal_id      INTEGER PRIMARY KEY REFERENCES source.journals(id) ON DELETE CASCADE,
    sentiment_score FLOAT,
    mood_label      TEXT,
    keywords        TEXT[],
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

-- +goose Down

DROP TABLE IF EXISTS source.journal_details;
