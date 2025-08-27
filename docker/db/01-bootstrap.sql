CREATE SCHEMA source;
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
values ('36ca3d17-0071-4526-a124-342fb025723e', 'jyablonski9@gmail.com', null, null, 'github', 'Consumer', now(), now(), 'UTC');

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

INSERT INTO journals (user_id, journal_text, mood_score, created_at, modified_at)
VALUES 
  ('36ca3d17-0071-4526-a124-342fb025723e', 
   'Today was a productive day. I managed to finish all my tasks and feel accomplished.', 8, now(), now()),
  
  ('36ca3d17-0071-4526-a124-342fb025723e', 
   'I felt a bit anxious during the meeting but tried to stay calm.', 4, now() - interval '1 day', now() - interval '1 day'),
  
  ('36ca3d17-0071-4526-a124-342fb025723e', 
   'Had a relaxing evening reading a good book and drinking tea.', 7, now() - interval '2 days', now() - interval '2 days'),
  
  ('36ca3d17-0071-4526-a124-342fb025723e', 
   'Struggled with motivation today, found it hard to focus.', 3, now() - interval '3 days', now() - interval '3 days'),
  
  ('36ca3d17-0071-4526-a124-342fb025723e', 
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

-- Indexes for performance  
CREATE INDEX idx_journal_topics_journal_id ON journal_topics(journal_id);
CREATE INDEX idx_journal_topics_topic_name ON journal_topics(topic_name);

-- Example of what the data might look like
INSERT INTO journal_topics (journal_id, topic_name, confidence, ml_model_version) VALUES
(1, 'productivity', 0.7234, 'v1.0.0'),
(1, 'accomplishment', 0.2156, 'v1.0.0'),
(2, 'anxiety', 0.8901, 'v1.0.0'),
(2, 'work_stress', 0.3245, 'v1.0.0');
