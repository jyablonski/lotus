import uuid

from django.contrib.auth.hashers import make_password
from django.db import migrations

TEST_PASSWORD = "testpass123"
SEEDED_USERS = (
    {
        "email": "product-test@lotus.dev",
        "username": "product-test@lotus.dev",
        "first_name": "Product",
        "last_name": "Tester",
        "group": "product",
        "role": "Consumer",
        "timezone": "America/Los_Angeles",
        "community_insights_opt_in": True,
        "community_location_opt_in": True,
        "community_country_code": "US",
        "community_region_code": "US-CA",
    },
    {
        "email": "mlops-test@lotus.dev",
        "username": "mlops-test@lotus.dev",
        "first_name": "ML",
        "last_name": "Ops",
        "group": "ml_ops",
        "role": "Consumer",
        "timezone": "UTC",
        "community_insights_opt_in": False,
        "community_location_opt_in": False,
        "community_country_code": None,
        "community_region_code": None,
    },
)


def seed_ml_model_admin_test_users(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    DjangoUser = apps.get_model("auth", "User")
    LotusUser = apps.get_model("core", "User")

    for user_data in SEEDED_USERS:
        group = Group.objects.get(name=user_data["group"])

        lotus_user, _ = LotusUser.objects.update_or_create(
            email=user_data["email"],
            defaults={
                "id": uuid.uuid5(uuid.NAMESPACE_DNS, f"lotus:{user_data['email']}"),
                "password": None,
                "salt": None,
                "oauth_provider": None,
                "role": user_data["role"],
                "timezone": user_data["timezone"],
                "community_insights_opt_in": user_data["community_insights_opt_in"],
                "community_location_opt_in": user_data["community_location_opt_in"],
                "community_country_code": user_data["community_country_code"],
                "community_region_code": user_data["community_region_code"],
            },
        )

        django_user, _ = DjangoUser.objects.update_or_create(
            username=user_data["username"],
            defaults={
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "is_staff": True,
                "is_superuser": False,
                "is_active": True,
                "password": make_password(TEST_PASSWORD),
            },
        )

        django_user.groups.add(group)

        if django_user.email != lotus_user.email:
            django_user.email = lotus_user.email
            django_user.save(update_fields=["email"])


def reverse_seed_ml_model_admin_test_users(apps, schema_editor):
    DjangoUser = apps.get_model("auth", "User")
    LotusUser = apps.get_model("core", "User")

    emails = [user_data["email"] for user_data in SEEDED_USERS]

    DjangoUser.objects.filter(username__in=emails).delete()
    LotusUser.objects.filter(email__in=emails).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0021_seed_community_pulse_flag"),
    ]

    operations = [
        migrations.RunPython(
            seed_ml_model_admin_test_users,
            reverse_seed_ml_model_admin_test_users,
        ),
    ]
