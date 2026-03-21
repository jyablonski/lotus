-- +goose Up
-- Reference-only migration for sqlc codegen. Actual schema managed by Django.
CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;

CREATE TABLE IF NOT EXISTS source.journal_embeddings (
    id SERIAL PRIMARY KEY,
    journal_id INTEGER NOT NULL REFERENCES source.journals(id) ON DELETE CASCADE,
    embedding vector(384) NOT NULL,
    model_version VARCHAR(50) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(journal_id, model_version)
);

CREATE INDEX IF NOT EXISTS idx_journal_embeddings_hnsw ON source.journal_embeddings
    USING hnsw (embedding vector_cosine_ops);

-- +goose Down
DROP INDEX IF EXISTS source.idx_journal_embeddings_hnsw;
DROP TABLE IF EXISTS source.journal_embeddings;
