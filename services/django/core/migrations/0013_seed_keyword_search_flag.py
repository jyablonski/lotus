from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_journal_search_vector_index"),
        ("waffle", "0004_update_everyone_nullbooleanfield"),
    ]

    operations = [
        migrations.RunSQL(
            sql="INSERT INTO source.waffle_flag (name, everyone, testing, superusers, staff, authenticated, languages, rollout, note, created, modified) VALUES ('keyword_search', true, false, false, false, false, '', false, 'Enable keyword-based tsvector search for all users', now(), now());",
            reverse_sql="DELETE FROM source.waffle_flag WHERE name = 'keyword_search';",
        ),
    ]
