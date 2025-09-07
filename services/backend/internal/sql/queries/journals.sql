-- name: CreateJournal :one
INSERT INTO source.journals(user_id, journal_text, mood_score)
VALUES ($1, $2, $3)
RETURNING *;

-- name: GetJournalsByUserId :many
SELECT * FROM source.journals WHERE user_id = $1 ORDER BY created_at DESC;

-- name: GetJournalById :one
SELECT * FROM source.journals WHERE id = $1;