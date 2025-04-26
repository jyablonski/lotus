-- name: CreateUser :one
INSERT INTO source.users(email, password, salt)
VALUES ($1, $2, $3)
RETURNING *;

-- name: GetUserByEmail :one
SELECT * FROM source.users WHERE email = $1;
