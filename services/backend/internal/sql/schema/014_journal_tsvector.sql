-- +goose Up

-- Add a tsvector column for full-text keyword search on journal entries.
ALTER TABLE source.journals ADD COLUMN search_vector tsvector;

-- Backfill existing rows.
UPDATE source.journals SET search_vector = to_tsvector('english', journal_text);

-- GIN index for fast full-text queries.
CREATE INDEX idx_journals_search_vector ON source.journals USING GIN (search_vector);

-- Auto-update the tsvector column on INSERT or UPDATE.
-- +goose StatementBegin
CREATE OR REPLACE FUNCTION source.journals_search_vector_trigger() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', NEW.journal_text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- +goose StatementEnd

CREATE TRIGGER trg_journals_search_vector
    BEFORE INSERT OR UPDATE OF journal_text ON source.journals
    FOR EACH ROW
    EXECUTE FUNCTION source.journals_search_vector_trigger();

-- +goose Down

DROP TRIGGER IF EXISTS trg_journals_search_vector ON source.journals;
DROP FUNCTION IF EXISTS source.journals_search_vector_trigger();
ALTER TABLE source.journals DROP COLUMN IF EXISTS search_vector;
