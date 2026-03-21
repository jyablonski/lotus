-- +goose Up
-- source.waffle_flag is managed by django-waffle migrations.
-- This schema definition exists only for sqlc code generation.

CREATE TABLE IF NOT EXISTS source.waffle_flag
(
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    everyone      BOOLEAN NOT NULL DEFAULT false,
    percent       NUMERIC(3,1),
    testing       BOOLEAN NOT NULL DEFAULT false,
    superusers    BOOLEAN NOT NULL DEFAULT true,
    staff         BOOLEAN NOT NULL DEFAULT false,
    authenticated BOOLEAN NOT NULL DEFAULT false,
    languages     TEXT NOT NULL DEFAULT '',
    rollout       BOOLEAN NOT NULL DEFAULT false,
    note          TEXT NOT NULL DEFAULT '',
    created       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modified      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- +goose Down

DROP TABLE IF EXISTS source.waffle_flag;
