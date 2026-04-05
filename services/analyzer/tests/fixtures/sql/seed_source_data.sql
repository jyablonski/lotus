-- Deterministic seed data for analyzer integration tests.
-- Keep this lightweight and focused on rows required by tests.

INSERT INTO source.users (
    id, email, password, salt, oauth_provider, role, created_at, modified_at, timezone
)
VALUES
    ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'alice.smith@example.com', null, null, 'google', 'Consumer', now() - interval '30 days', now() - interval '30 days', 'America/New_York'),
    ('00000000-0000-0000-0000-000000000001', 'e2e-test@lotus.dev', null, null, null, 'Consumer', now(), now(), 'UTC'),
    ('00000000-0000-0000-0000-000000000002', 'e2e-admin@lotus.dev', null, null, null, 'Admin', now(), now(), 'UTC')
ON CONFLICT (email) DO NOTHING;

INSERT INTO source.journals (
    id, user_id, journal_text, mood_score, created_at, modified_at
)
VALUES
    (1, 'a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'Today was a productive day. I managed to finish all my tasks and feel accomplished.', 8, now(), now()),
    (2, 'a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'I felt a bit anxious during the meeting but tried to stay calm.', 4, now() - interval '1 day', now() - interval '1 day'),
    (3, 'a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'Had a relaxing evening reading a good book and drinking tea.', 7, now() - interval '2 days', now() - interval '2 days'),
    (4, 'a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'Struggled with motivation today, found it hard to focus.', 3, now() - interval '3 days', now() - interval '3 days'),
    (5, 'a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'Feeling grateful for the support from friends and family.', 9, now() - interval '4 days', now() - interval '4 days')
ON CONFLICT (id) DO NOTHING;

INSERT INTO source.journal_sentiments (
    journal_id, sentiment, confidence, confidence_level, is_reliable, ml_model_version, all_scores
)
VALUES
    (1, 'positive', 0.8234, 'high', TRUE, 'v1.0.0', '{"positive": 0.8234, "negative": 0.1234, "neutral": 0.0532}')
ON CONFLICT (journal_id, ml_model_version) DO NOTHING;

SELECT setval(
    'source.journals_id_seq',
    COALESCE((SELECT MAX(id) FROM source.journals), 1),
    true
);

SELECT setval(
    'source.journal_sentiments_id_seq',
    COALESCE((SELECT MAX(id) FROM source.journal_sentiments), 1),
    true
);
