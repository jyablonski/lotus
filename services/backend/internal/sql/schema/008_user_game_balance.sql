-- +goose Up

CREATE TABLE IF NOT EXISTS source.user_game_balances (
    id          SERIAL PRIMARY KEY,
    user_id     UUID NOT NULL UNIQUE REFERENCES source.users(id) ON DELETE CASCADE,
    balance     INTEGER NOT NULL DEFAULT 100,
    created_at  TIMESTAMP DEFAULT NOW() NOT NULL,
    modified_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- +goose Down

DROP TABLE IF EXISTS source.user_game_balances;
