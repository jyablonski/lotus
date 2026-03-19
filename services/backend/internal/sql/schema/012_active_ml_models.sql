-- +goose Up
-- active_ml_models is managed by Django migrations.
-- This schema definition exists only for sqlc code generation.

CREATE TABLE IF NOT EXISTS active_ml_models
(
    id         SERIAL PRIMARY KEY,
    ml_model   VARCHAR(255) NOT NULL UNIQUE,
    is_enabled BOOLEAN      NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    modified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- +goose Down

DROP TABLE IF EXISTS active_ml_models;
