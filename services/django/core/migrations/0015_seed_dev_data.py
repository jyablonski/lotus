from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_seed_feature_flags"),
    ]

    operations = [
        # Seed users
        migrations.RunSQL(
            sql="""
                INSERT INTO source.users (id, email, password, salt, oauth_provider, role, created_at, modified_at, timezone)
                VALUES
                    ('a91b114d-b3de-4fe6-b162-039c9850c06b', 'jyablonski9@gmail.com', null, null, 'github', 'Admin', now(), now(), 'UTC'),
                    ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'alice.smith@example.com', null, null, 'google', 'Consumer', now() - interval '30 days', now() - interval '30 days', 'America/New_York'),
                    ('b8e4f9c3-5e02-4d4b-a03f-2c9d6e7f8a9b', 'bob.jones@example.com', 'hashed_password_123', 'salt_123', null, 'Consumer', now() - interval '60 days', now() - interval '60 days', 'America/Los_Angeles'),
                    ('c9f5a0d4-6f13-4e5c-b14f-3d0e7f8a9b0c', 'carol.white@example.com', null, null, 'github', 'Premium', now() - interval '90 days', now() - interval '90 days', 'Europe/London'),
                    ('d0a6b1e5-7024-4f6d-c25e-4e1f8a9b0c1d', 'david.brown@example.com', 'hashed_password_456', 'salt_456', null, 'Admin', now() - interval '120 days', now() - interval '120 days', 'UTC'),
                    ('00000000-0000-0000-0000-000000000001', 'e2e-test@lotus.dev', null, null, null, 'Consumer', now(), now(), 'UTC'),
                    ('00000000-0000-0000-0000-000000000002', 'e2e-admin@lotus.dev', null, null, null, 'Admin', now(), now(), 'UTC')
                ON CONFLICT (email) DO NOTHING;
            """,
            reverse_sql="DELETE FROM source.users WHERE email IN ('jyablonski9@gmail.com', 'alice.smith@example.com', 'bob.jones@example.com', 'carol.white@example.com', 'david.brown@example.com', 'e2e-test@lotus.dev', 'e2e-admin@lotus.dev');",
        ),
        # Seed journals
        migrations.RunSQL(
            sql="""
                INSERT INTO source.journals (user_id, journal_text, mood_score, created_at, modified_at)
                VALUES
                    ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'Today was a productive day. I managed to finish all my tasks and feel accomplished.', 8, now(), now()),
                    ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'I felt a bit anxious during the meeting but tried to stay calm.', 4, now() - interval '1 day', now() - interval '1 day'),
                    ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'Had a relaxing evening reading a good book and drinking tea.', 7, now() - interval '2 days', now() - interval '2 days'),
                    ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'Struggled with motivation today, found it hard to focus.', 3, now() - interval '3 days', now() - interval '3 days'),
                    ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', 'Feeling grateful for the support from friends and family.', 9, now() - interval '4 days', now() - interval '4 days'),
                    ('00000000-0000-0000-0000-000000000002', 'Working on the new feature deployment today. Everything went smoothly.', 8, now(), now()),
                    ('00000000-0000-0000-0000-000000000002', 'Had a tough debugging session but finally found the root cause.', 5, now() - interval '1 day', now() - interval '1 day'),
                    ('00000000-0000-0000-0000-000000000002', 'Great team standup this morning. Feeling motivated and energized.', 9, now() - interval '2 days', now() - interval '2 days'),
                    ('00000000-0000-0000-0000-000000000001', 'Started learning something new today. It was challenging but rewarding.', 7, now(), now()),
                    ('00000000-0000-0000-0000-000000000001', 'Feeling a bit overwhelmed with everything going on lately.', 4, now() - interval '1 day', now() - interval '1 day'),
                    ('00000000-0000-0000-0000-000000000001', 'Went for a long walk in the park. Nature always helps me clear my mind.', 8, now() - interval '2 days', now() - interval '2 days');
            """,
            reverse_sql="DELETE FROM source.journals WHERE user_id IN ('a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002');",
        ),
        # Seed journal topics
        migrations.RunSQL(
            sql="""
                INSERT INTO source.journal_topics (journal_id, topic_name, subtopic_name, confidence, ml_model_version)
                VALUES
                    (1, 'work', 'deadlines and workload pressure', 0.7234, 'v1.0.0'),
                    (1, 'growth', 'goals and personal motivation', 0.2156, 'v1.0.0'),
                    (2, 'wellbeing', 'anxiety and worry about the future', 0.8901, 'v1.0.0'),
                    (2, 'work', 'stress and feeling overwhelmed', 0.3245, 'v1.0.0'),
                    (6, 'work', 'project deployments', 0.8100, 'v1.0.0'),
                    (7, 'growth', 'problem solving and persistence', 0.7500, 'v1.0.0'),
                    (8, 'wellbeing', 'team collaboration and energy', 0.6800, 'v1.0.0');
            """,
            reverse_sql="DELETE FROM source.journal_topics WHERE ml_model_version = 'v1.0.0' AND journal_id IN (1, 2, 6, 7, 8);",
        ),
        # Seed journal sentiments
        migrations.RunSQL(
            sql="""
                INSERT INTO source.journal_sentiments (journal_id, sentiment, confidence, confidence_level, is_reliable, ml_model_version, all_scores)
                VALUES
                    (1, 'positive', 0.8234, 'high', TRUE, 'v1.0.0', '{"positive": 0.8234, "negative": 0.1234, "neutral": 0.0532}'),
                    (2, 'negative', 0.7891, 'high', TRUE, 'v1.0.0', '{"positive": 0.0823, "negative": 0.7891, "neutral": 0.1286}');
            """,
            reverse_sql="DELETE FROM source.journal_sentiments WHERE ml_model_version = 'v1.0.0' AND journal_id IN (1, 2);",
        ),
        # Truncate function for backend integration tests
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION source.truncate_integration_tables()
                RETURNS void
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    TRUNCATE source.journal_embeddings, source.journal_sentiments, source.journal_topics,
                             source.journal_details, source.journals, source.user_game_bets,
                             source.user_game_balances, source.users
                    RESTART IDENTITY CASCADE;
                END;
                $$;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS source.truncate_integration_tables();",
        ),
    ]
