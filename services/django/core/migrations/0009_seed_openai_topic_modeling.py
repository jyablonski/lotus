from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_journaltopic_subtopic_name"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                UPDATE active_ml_models
                SET ml_model = 'openai_topic_modeling', is_enabled = false, modified_at = NOW()
                WHERE ml_model = 'topic_modeling';
            """,
            reverse_sql="""
                UPDATE active_ml_models
                SET ml_model = 'topic_modeling', modified_at = NOW()
                WHERE ml_model = 'openai_topic_modeling';
            """,
        ),
    ]
