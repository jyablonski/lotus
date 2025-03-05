CREATE SCHEMA source;
SET search_path TO source;

DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users
(
    id serial primary key,
    username varchar not null,
    password varchar not null,
    email varchar not null,
    salt varchar not null,
	role varchar default 'Consumer' not null,
    created_at timestamp default now() not null,
	modified_at timestamp default now() not null,
	timezone varchar default 'UTC' not null
);
