-- +goose Up

CREATE TABLE IF NOT EXISTS source.user_game_bets (
    id          SERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES source.users(id) ON DELETE CASCADE,
    zone        VARCHAR(10) NOT NULL,
    amount      INTEGER NOT NULL,
    roll_result INTEGER NOT NULL,
    payout      INTEGER NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_game_bets_user_created
    ON source.user_game_bets (user_id, created_at DESC);

-- +goose Down

DROP TABLE IF EXISTS source.user_game_bets;
