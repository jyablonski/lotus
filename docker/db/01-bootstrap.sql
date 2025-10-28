CREATE SCHEMA source;
CREATE SCHEMA core;
CREATE SCHEMA staging;
SET search_path TO source;

-- this has to come after setting the schema search path ;-)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users
(
    id UUID primary key default uuid_generate_v4(),
    email varchar not null unique,
    password varchar,
    salt varchar,
    oauth_provider varchar,
	role varchar default 'Consumer' not null,
    created_at timestamp default now() not null,
	modified_at timestamp default now() not null,
	timezone varchar default 'UTC' not null
);

insert into users (id, email, password, salt, oauth_provider, role, created_at, modified_at, timezone)
values
  ('a91b114d-b3de-4fe6-b162-039c9850c06b', 'jyablonski9@gmail.com', null, null, 'github', 'Consumer', now(), now(), 'UTC'),
  ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'alice.smith@example.com', null, null, 'google', 'Consumer', now() - interval '30 days', now() - interval '30 days', 'America/New_York'),
  ('b8e4f9c3-5e02-4d4b-a03f-2c9d6e7f8a9b', 'bob.jones@example.com', 'hashed_password_123', 'salt_123', null, 'Consumer', now() - interval '60 days', now() - interval '60 days', 'America/Los_Angeles'),
  ('c9f5a0d4-6f13-4e5c-b14f-3d0e7f8a9b0c', 'carol.white@example.com', null, null, 'github', 'Premium', now() - interval '90 days', now() - interval '90 days', 'Europe/London'),
  ('d0a6b1e5-7024-4f6d-c25e-4e1f8a9b0c1d', 'david.brown@example.com', 'hashed_password_456', 'salt_456', null, 'Admin', now() - interval '120 days', now() - interval '120 days', 'UTC');

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

CREATE INDEX idx_journals_user_id_created_at ON source.journals(user_id, created_at DESC);

INSERT INTO journals (user_id, journal_text, mood_score, created_at, modified_at)
VALUES
  ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a',
   'Today was a productive day. I managed to finish all my tasks and feel accomplished.', 8, now(), now()),

  ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a',
   'I felt a bit anxious during the meeting but tried to stay calm.', 4, now() - interval '1 day', now() - interval '1 day'),

  ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a',
   'Had a relaxing evening reading a good book and drinking tea.', 7, now() - interval '2 days', now() - interval '2 days'),

  ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a',
   'Struggled with motivation today, found it hard to focus.', 3, now() - interval '3 days', now() - interval '3 days'),

  ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a',
   'Feeling grateful for the support from friends and family.', 9, now() - interval '4 days', now() - interval '4 days');

-- table for original analyzer implementation
CREATE TABLE IF NOT EXISTS journal_details (
    journal_id INTEGER PRIMARY KEY REFERENCES journals(id) ON DELETE CASCADE,
    sentiment_score FLOAT,
    mood_label TEXT,
    keywords TEXT[],
    created_at timestamp default now() not null,
    modified_at timestamp default now() not null
);

-- topics table for mlflow / experiment workflow
CREATE TABLE IF NOT EXISTS journal_topics (
    id SERIAL PRIMARY KEY,
    journal_id INTEGER REFERENCES journals(id) ON DELETE CASCADE,
    topic_name VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    ml_model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_journal_topics_journal_id ON journal_topics(journal_id);
CREATE INDEX idx_journal_topics_topic_name ON journal_topics(topic_name);

INSERT INTO journal_topics (journal_id, topic_name, confidence, ml_model_version) VALUES
(1, 'productivity', 0.7234, 'v1.0.0'),
(1, 'accomplishment', 0.2156, 'v1.0.0'),
(2, 'anxiety', 0.8901, 'v1.0.0'),
(2, 'work_stress', 0.3245, 'v1.0.0');


CREATE TABLE IF NOT EXISTS source.journal_sentiments (
    id SERIAL PRIMARY KEY,
    journal_id INTEGER REFERENCES journals(id) ON DELETE CASCADE,
    sentiment VARCHAR(20) NOT NULL CHECK (sentiment IN ('positive', 'negative', 'neutral', 'uncertain')),
    confidence DECIMAL(5,4) NOT NULL,
    confidence_level VARCHAR(10) NOT NULL CHECK (confidence_level IN ('high', 'medium', 'low')),
    is_reliable BOOLEAN NOT NULL DEFAULT TRUE,
    ml_model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Optional: Store individual sentiment scores as JSON
    all_scores JSONB,

    -- Ensure only one sentiment analysis per journal entry per model version
    UNIQUE(journal_id, ml_model_version)
);

INSERT INTO source.journal_sentiments (journal_id, sentiment, confidence, confidence_level, is_reliable, ml_model_version, all_scores) VALUES
(1, 'positive', 0.8234, 'high', TRUE, 'v1.0.0', '{"positive": 0.8234, "negative": 0.1234, "neutral": 0.0532}'),
(2, 'negative', 0.7891, 'high', TRUE, 'v1.0.0', '{"positive": 0.0823, "negative": 0.7891, "neutral": 0.1286}');
