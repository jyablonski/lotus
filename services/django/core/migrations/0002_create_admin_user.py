from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_admin_user(apps, schema_editor):
    """Create admin user in both Django auth and Lotus users table."""
    # Get models using apps.get_model (Django best practice for migrations)
    User = apps.get_model("auth", "User")
    LotusUser = apps.get_model("core", "User")

    # Create Django User
    django_user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin",
            "is_staff": True,
            "is_superuser": True,
            "password": make_password("admin"),
        },
    )

    # Update password and permissions if user already existed
    if not created:
        django_user.password = make_password("admin")
        django_user.email = "admin"
        django_user.is_staff = True
        django_user.is_superuser = True
        django_user.save()

    # Ensure Lotus User exists with Admin role
    lotus_user, created = LotusUser.objects.get_or_create(
        email="admin", defaults={"role": "Admin", "timezone": "UTC"}
    )

    # Update role if user already existed
    if not created and lotus_user.role != "Admin":
        lotus_user.role = "Admin"
        lotus_user.save()


def reverse_create_admin_user(apps, schema_editor):
    """Remove admin user if migration is reversed."""
    User = apps.get_model("auth", "User")
    LotusUser = apps.get_model("core", "User")

    User.objects.filter(username="admin").delete()
    LotusUser.objects.filter(email="admin").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_admin_user, reverse_create_admin_user),
    ]
