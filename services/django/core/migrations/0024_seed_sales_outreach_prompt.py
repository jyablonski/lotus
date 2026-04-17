from django.db import migrations

SALES_GROUP_NAME = "sales"
SALES_OUTREACH_APPLICATION = "sales_outreach"
SALES_OUTREACH_PROMPT = (
    "You are a helpful sales assistant. Write a concise, friendly outreach "
    "message (max 4 sentences) introducing Lotus, a journaling + analytics "
    "platform, to a prospective customer. Keep the tone warm and avoid "
    "jargon."
)


def seed_sales_outreach_prompt(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    StakeholderPrompt = apps.get_model("core", "StakeholderPrompt")

    sales_group, _ = Group.objects.get_or_create(name=SALES_GROUP_NAME)

    StakeholderPrompt.objects.update_or_create(
        application=SALES_OUTREACH_APPLICATION,
        defaults={
            "stakeholder_group": sales_group,
            "prompt": SALES_OUTREACH_PROMPT,
        },
    )


def reverse_seed_sales_outreach_prompt(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    StakeholderPrompt = apps.get_model("core", "StakeholderPrompt")

    StakeholderPrompt.objects.filter(application=SALES_OUTREACH_APPLICATION).delete()
    Group.objects.filter(name=SALES_GROUP_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("core", "0023_stakeholder_prompts"),
    ]

    operations = [
        migrations.RunPython(
            seed_sales_outreach_prompt,
            reverse_seed_sales_outreach_prompt,
        ),
    ]
