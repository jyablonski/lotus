-- name: CreateJournalExport :one
INSERT INTO source.journal_exports (user_id, format, status)
VALUES ($1, $2, 'pending')
RETURNING *;

-- name: GetJournalExport :one
SELECT * FROM source.journal_exports
WHERE id = $1 AND user_id = $2;

-- name: UpdateJournalExportProcessing :one
UPDATE source.journal_exports
SET status = 'processing'
WHERE id = $1
RETURNING *;

-- name: UpdateJournalExportComplete :one
UPDATE source.journal_exports
SET status       = 'complete',
    content      = $2,
    completed_at = now()
WHERE id = $1
RETURNING *;

-- name: UpdateJournalExportFailed :one
UPDATE source.journal_exports
SET status    = 'failed',
    error_msg = $2
WHERE id = $1
RETURNING *;
