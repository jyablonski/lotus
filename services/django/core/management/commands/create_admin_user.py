from django.contrib.auth.models import User as DjangoUser
from django.core.management.base import BaseCommand

from core.models import User as LotusUser


class Command(BaseCommand):
    help = "Create an admin user for Django admin interface"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email address of the admin user (must exist in users table)",
        )
        parser.add_argument(
            "--password",
            type=str,
            required=True,
            help="Password for Django admin login",
        )

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]

        # Check if Lotus user exists and has Admin role
        try:
            lotus_user = LotusUser.objects.get(email=email)
            if lotus_user.role != "Admin":
                self.stdout.write(
                    self.style.ERROR(
                        f"User {email} exists but does not have Admin role. "
                        f"Current role: {lotus_user.role}"
                    )
                )
                return
        except LotusUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"User {email} does not exist in the users table. "
                    "Please create the user first with Admin role."
                )
            )
            return

        # Create or update Django user
        django_user, created = DjangoUser.objects.get_or_create(
            username=email, defaults={"email": email}
        )

        if not created:
            django_user.email = email
            django_user.save()
            self.stdout.write(
                self.style.WARNING(f"Updated existing Django user: {email}")
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"Created Django user: {email}"))

        # Set password
        django_user.set_password(password)
        django_user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created/updated admin user: {email}\n"
                f"You can now log in at /admin/ with this email and password."
            )
        )
