-- +goose Up

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS source;


-- +goose Down

DROP SCHEMA source;

DROP EXTENSION IF EXISTS "uuid-ossp";
