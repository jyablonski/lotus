-- +goose Up

CREATE SCHEMA IF NOT EXISTS source;


-- +goose Down

DROP SCHEMA source;