CREATE SCHEMA source;
SET search_path TO source;

-- this has to come after setting the schema search path ;-)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users
(
    id UUID primary key default uuid_generate_v4(),
    email varchar not null unique,
    password varchar not null,
    salt varchar not null,
	role varchar default 'Consumer' not null,
    created_at timestamp default now() not null,
	modified_at timestamp default now() not null,
	timezone varchar default 'UTC' not null
);

DROP TABLE IF EXISTS journals;
CREATE TABLE IF NOT EXISTS journals
(
    id serial primary key,
    user_id UUID not null,
    journal_text text not null,
    mood_score integer,
    created_at timestamp default now() not null,
    modified_at timestamp default now() not null
);
