-- name: CreateUser :one
INSERT INTO source.users(email, password, salt)
VALUES ($1, $2, $3)
RETURNING *;

-- name: CreateUserOauth :one
INSERT INTO source.users(email, oauth_provider)
VALUES ($1, $2)
RETURNING *;

-- name: GetUserByEmail :one
SELECT * FROM source.users WHERE email = $1;

-- name: GetUserById :one
SELECT * FROM source.users WHERE id = $1;

-- name: UpdateUserTimezone :one
UPDATE source.users
SET timezone = $2, modified_at = NOW()
WHERE id = $1
RETURNING *;

-- name: GetCommunitySettingsByUserId :one
SELECT
    id,
    community_insights_opt_in,
    community_location_opt_in,
    community_country_code,
    community_region_code,
    modified_at
FROM source.users
WHERE id = $1;

-- name: UpdateCommunitySettingsByUserId :one
UPDATE source.users
SET
    community_insights_opt_in = $2,
    community_location_opt_in = $3,
    community_country_code = $4,
    community_region_code = $5,
    modified_at = NOW()
WHERE id = $1
RETURNING *;

-- name: DeleteUserById :exec
DELETE FROM source.users WHERE id = $1;
