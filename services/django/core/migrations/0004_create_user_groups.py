# Generated manually

from django.db import migrations


def create_user_groups(apps, schema_editor):
    """Create user groups: product, ml_ops, infrastructure, and engineering."""
    Group = apps.get_model("auth", "Group")

    groups = ["product", "ml_ops", "infrastructure", "engineering"]

    for group_name in groups:
        Group.objects.get_or_create(name=group_name)


def reverse_create_user_groups(apps, schema_editor):
    """Remove the user groups."""
    Group = apps.get_model("auth", "Group")

    groups = ["product", "ml_ops", "infrastructure", "engineering"]

    for group_name in groups:
        Group.objects.filter(name=group_name).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_create_admin_user"),
    ]

    operations = [
        migrations.RunPython(create_user_groups, reverse_create_user_groups),
    ]
