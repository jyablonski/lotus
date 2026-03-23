from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_seed_keyword_search_flag"),
        ("waffle", "0004_update_everyone_nullbooleanfield"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                INSERT INTO source.waffle_flag (name, everyone, testing, superusers, staff, authenticated, languages, rollout, note, created, modified)
                VALUES
                    ('frontend_admin', false, false, true, true, false, '', false, 'Show admin link on profile when user role is Admin', now(), now()),
                    ('semantic_search', false, false, true, true, false, '', false, 'Enable semantic search toggle on journal page', now(), now()),
                    ('frontend_show_tags', false, false, true, true, false, '', false, 'Show OpenAI topic tags on journal entries', now(), now())
                ON CONFLICT (name) DO NOTHING;
            """,
            reverse_sql="""
                DELETE FROM source.waffle_flag WHERE name IN ('frontend_admin', 'semantic_search', 'frontend_show_tags');
            """,
        ),
    ]
