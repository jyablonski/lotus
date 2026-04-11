from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0020_user_community_country_code_and_more"),
        ("waffle", "0004_update_everyone_nullbooleanfield"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                INSERT INTO source.waffle_flag (
                    name,
                    everyone,
                    testing,
                    superusers,
                    staff,
                    authenticated,
                    languages,
                    rollout,
                    note,
                    created,
                    modified
                )
                VALUES (
                    'community_pulse',
                    false,
                    false,
                    false,
                    false,
                    false,
                    '',
                    false,
                    'Show Community Pulse surfaces in the frontend',
                    now(),
                    now()
                )
                ON CONFLICT (name) DO NOTHING;
            """,
            reverse_sql="""
                DELETE FROM source.waffle_flag WHERE name = 'community_pulse';
            """,
        ),
    ]
