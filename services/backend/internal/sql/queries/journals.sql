-- name: CreateJournal :one
INSERT INTO source.journals(user_id, journal_text, mood_score)
VALUES ($1, $2, $3)
RETURNING *;

-- name: GetJournalsByUserId :many
SELECT * FROM source.journals WHERE user_id = $1 ORDER BY created_at DESC;

-- name: GetJournalsByUserIdPaginated :many
SELECT * FROM source.journals
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT $2 OFFSET $3;

-- name: GetJournalCountByUserId :one
SELECT COUNT(*) FROM source.journals WHERE user_id = $1;

-- name: GetJournalById :one
SELECT * FROM source.journals WHERE id = $1;

-- name: UpdateJournalForUser :execrows
UPDATE source.journals
SET journal_text = $1, mood_score = $2, modified_at = NOW()
WHERE id = $3 AND user_id = $4;

-- name: DeleteJournalForUser :execrows
DELETE FROM source.journals WHERE id = $1 AND user_id = $2;

-- name: SearchJournalsSemantic :many
SELECT
    j.id,
    j.journal_text,
    j.mood_score,
    j.created_at,
    (1 - (je.embedding <=> sqlc.arg(embedding_literal)::public.vector))::float8 AS similarity
FROM source.journals j
INNER JOIN source.journal_embeddings je ON j.id = je.journal_id
WHERE j.user_id = sqlc.arg(user_id)
ORDER BY je.embedding <=> sqlc.arg(embedding_literal)::public.vector
LIMIT sqlc.arg(result_limit);

-- name: SearchJournalsKeyword :many
SELECT
    j.id,
    j.journal_text,
    j.mood_score,
    j.created_at,
    ts_rank(j.search_vector, plainto_tsquery('english', sqlc.arg(query_text)))::float8 AS rank
FROM source.journals j
WHERE j.user_id = sqlc.arg(user_id)
  AND j.search_vector @@ plainto_tsquery('english', sqlc.arg(query_text))
ORDER BY ts_rank(j.search_vector, plainto_tsquery('english', sqlc.arg(query_text))) DESC
LIMIT sqlc.arg(result_limit);
