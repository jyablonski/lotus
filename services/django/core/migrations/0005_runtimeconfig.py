# Generated manually

from django.db import migrations, models
import django.db.models.functions.datetime


# for example of how to use this:
# go: `services/backend/internal/grpc/util_service.go`
class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_create_user_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name="RuntimeConfig",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("key", models.CharField(max_length=255, unique=True)),
                ("value", models.JSONField(default=dict)),
                (
                    "service",
                    models.CharField(
                        choices=[
                            ("analyzer", "Analyzer"),
                            ("backend", "Backend"),
                            ("dagster", "Dagster"),
                            ("dbt", "dbt"),
                            ("django", "Django"),
                            ("experiments", "Experiments"),
                            ("frontend", "Frontend"),
                        ],
                        max_length=50,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
                (
                    "modified_at",
                    models.DateTimeField(
                        auto_now=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
            ],
            options={
                "db_table": "runtime_config",
                "ordering": ["key"],
                "verbose_name": "runtime config",
                "verbose_name_plural": "runtime config",
            },
        ),
        # Seed example runtime config entry
        migrations.RunSQL(
            sql="""
                INSERT INTO runtime_config (key, value, service, description, created_at, modified_at)
                VALUES (
                    'ml',
                    '{"ENABLED": false, "LAST_RUN_TIMESTAMP": "2026-02-26T10:10:10Z"}',
                    'analyzer',
                    'Example Column for Analyzer Service',
                    NOW(),
                    NOW()
                );
            """,
            reverse_sql="DELETE FROM runtime_config WHERE key = 'ml';",
        ),
    ]
