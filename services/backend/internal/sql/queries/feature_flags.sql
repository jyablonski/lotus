-- name: GetActiveFeatureFlags :many
SELECT * FROM source.waffle_flag;

-- name: GetFeatureFlagByName :one
SELECT * FROM source.waffle_flag WHERE name = $1;
