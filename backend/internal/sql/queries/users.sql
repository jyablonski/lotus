-- name: CreateUser :one
INSERT INTO source.users(username, password, email, salt)
VALUES ($1, $2, $3, $4)
RETURNING *;

-- name: GetUserByUsername :one
SELECT * FROM source.users WHERE username = $1;
