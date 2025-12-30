# Generated manually

from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_admin_user(apps, schema_editor):
    """Create an admin user for Django admin interface."""
    User = apps.get_model("core", "User")
    DjangoUser = apps.get_model("auth", "User")

    admin_email = "admin"
    admin_password = "password"

    # Create or get Lotus User with Admin role
    lotus_user, created = User.objects.get_or_create(
        email=admin_email,
        defaults={
            "role": "Admin",
            "timezone": "UTC",
        },
    )

    # Update role if user already exists
    if not created and lotus_user.role != "Admin":
        lotus_user.role = "Admin"
        lotus_user.save()

    # Create or update Django User
    django_user, created = DjangoUser.objects.get_or_create(
        username=admin_email,
        defaults={
            "email": admin_email,
            "is_staff": True,
            "is_superuser": True,
            "password": make_password(admin_password),
        },
    )

    if not created:
        django_user.email = admin_email
        django_user.is_staff = True
        django_user.is_superuser = True
        django_user.password = make_password(admin_password)
        django_user.save()


def reverse_create_admin_user(apps, schema_editor):
    """Remove the admin user."""
    DjangoUser = apps.get_model("auth", "User")

    admin_email = "admin"

    # Delete Django User
    DjangoUser.objects.filter(username=admin_email).delete()

    # Note: We don't delete the Lotus User to preserve data


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_seed_data"),
    ]

    operations = [
        migrations.RunPython(create_admin_user, reverse_create_admin_user),
    ]
