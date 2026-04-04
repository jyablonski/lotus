-- +goose Up

CREATE TYPE source.export_format AS ENUM ('csv', 'markdown');
CREATE TYPE source.export_status AS ENUM ('pending', 'processing', 'complete', 'failed');

CREATE TABLE IF NOT EXISTS source.journal_exports
(
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID                   NOT NULL,
    format       source.export_format   NOT NULL DEFAULT 'csv',
    status       source.export_status   NOT NULL DEFAULT 'pending',
    content      TEXT,
    error_msg    TEXT,
    created_at   TIMESTAMP              NOT NULL DEFAULT now(),
    completed_at TIMESTAMP
);


-- +goose Down

DROP TABLE IF EXISTS source.journal_exports;
DROP TYPE IF EXISTS source.export_status;
DROP TYPE IF EXISTS source.export_format;
