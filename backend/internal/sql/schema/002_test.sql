-- +goose Up

CREATE TABLE IF NOT EXISTS source.users
(
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email varchar not null,
    password varchar not null,
    salt varchar not null,
	role varchar default 'Consumer' not null,
    created_at timestamp default now() not null,
	modified_at timestamp default now() not null,
	timezone varchar default 'UTC' not null
);


-- +goose Down

DROP TABLE source.users;
