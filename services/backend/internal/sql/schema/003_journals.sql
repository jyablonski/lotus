-- +goose Up

CREATE TABLE IF NOT EXISTS source.journals
(
    id serial primary key,
    user_id UUID not null,
    journal_text text not null,
    mood_score integer,
    created_at timestamp default now() not null,
    modified_at timestamp default now() not null
);


-- +goose Down

DROP TABLE source.journals;
