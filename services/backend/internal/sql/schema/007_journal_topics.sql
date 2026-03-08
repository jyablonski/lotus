-- +goose Up

CREATE TABLE IF NOT EXISTS source.journal_topics (
    id SERIAL PRIMARY KEY,
    journal_id INTEGER NOT NULL REFERENCES source.journals(id) ON DELETE CASCADE,
    topic_name VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    ml_model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_journal_topics_journal_id ON source.journal_topics(journal_id);
CREATE INDEX IF NOT EXISTS idx_journal_topics_topic_name ON source.journal_topics(topic_name);

-- +goose Down

DROP TABLE IF EXISTS source.journal_topics;
