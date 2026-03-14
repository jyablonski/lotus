-- name: GetUserGameBalance :one
SELECT * FROM source.user_game_balances WHERE user_id = $1;

-- name: UpsertUserGameBalance :one
INSERT INTO source.user_game_balances (user_id, balance)
VALUES ($1, $2)
ON CONFLICT (user_id) DO UPDATE
    SET balance     = EXCLUDED.balance,
        modified_at = NOW()
RETURNING *;
