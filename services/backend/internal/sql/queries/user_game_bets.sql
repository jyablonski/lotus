-- name: InsertUserGameBet :one
INSERT INTO source.user_game_bets (user_id, zone, amount, roll_result, payout)
VALUES ($1, $2, $3, $4, $5)
RETURNING *;

-- name: GetUserGameBets :many
SELECT * FROM source.user_game_bets
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT $2 OFFSET $3;
