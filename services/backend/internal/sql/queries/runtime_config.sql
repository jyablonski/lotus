-- name: GetRuntimeConfigByKey :one
SELECT * FROM source.runtime_config WHERE key = $1;

-- name: UpsertRuntimeConfigValue :one
INSERT INTO source.runtime_config (key, value, service, description)
VALUES ($1, $2, $3, $4)
ON CONFLICT (key)
DO UPDATE SET value = $2, modified_at = NOW()
RETURNING *;
