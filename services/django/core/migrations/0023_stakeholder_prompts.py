from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.datetime

import core.models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("core", "0022_seed_ml_model_admin_test_users"),
    ]

    operations = [
        migrations.CreateModel(
            name="StakeholderPrompt",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_default=core.models.UUIDGenerateV4(),
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("application", models.CharField(max_length=64, unique=True)),
                ("prompt", models.TextField()),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
                (
                    "stakeholder_group",
                    models.ForeignKey(
                        db_column="stakeholder_group_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="stakeholder_prompts",
                        to="auth.group",
                    ),
                ),
            ],
            options={
                "db_table": "stakeholder_prompts",
                "ordering": ["application"],
            },
        ),
        migrations.CreateModel(
            name="StakeholderPromptResponse",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_default=core.models.UUIDGenerateV4(),
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("model", models.CharField(max_length=64)),
                ("response", models.TextField()),
                (
                    "run_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
                (
                    "stakeholder_prompt",
                    models.ForeignKey(
                        db_column="stakeholder_prompt_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="responses",
                        to="core.stakeholderprompt",
                    ),
                ),
            ],
            options={
                "db_table": "stakeholder_prompt_responses",
                "ordering": ["-run_at"],
                "indexes": [
                    models.Index(
                        fields=["stakeholder_prompt", "-run_at"],
                        name="idx_spr_prompt_run_at",
                    ),
                ],
            },
        ),
    ]
