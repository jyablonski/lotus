from django.contrib.auth.models import User as DjangoUser
from django.core.management.base import BaseCommand

from core.models import User as LotusUser


class Command(BaseCommand):
    help = "Sync all existing Lotus Users to Django Users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        lotus_users = LotusUser.objects.all()

        self.stdout.write(f"Found {lotus_users.count()} Lotus Users to sync")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for lotus_user in lotus_users:
            django_user_exists = DjangoUser.objects.filter(
                username=lotus_user.email
            ).exists()

            if django_user_exists:
                django_user = DjangoUser.objects.get(username=lotus_user.email)
                needs_update = False

                # Check if email needs updating
                if django_user.email != lotus_user.email:
                    needs_update = True
                    if not dry_run:
                        django_user.email = lotus_user.email

                # Check if admin privileges need updating
                is_admin = lotus_user.role == "Admin"
                if django_user.is_staff != is_admin or django_user.is_superuser != is_admin:
                    needs_update = True
                    if not dry_run:
                        django_user.is_staff = is_admin
                        django_user.is_superuser = is_admin

                if needs_update:
                    if not dry_run:
                        django_user.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Updated Django User for {lotus_user.email} "
                            f"(role: {lotus_user.role}, is_staff: {is_admin})"
                        )
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        f"  - Skipped {lotus_user.email} (already in sync)"
                    )
            else:
                if not dry_run:
                    django_user = DjangoUser.objects.create(
                        username=lotus_user.email,
                        email=lotus_user.email,
                        is_staff=(lotus_user.role == "Admin"),
                        is_superuser=(lotus_user.role == "Admin"),
                    )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  + Created Django User for {lotus_user.email} "
                        f"(role: {lotus_user.role}, is_staff: {lotus_user.role == 'Admin'})"
                    )
                )

        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes made"))
        self.stdout.write(
            f"Summary: {created_count} created, {updated_count} updated, {skipped_count} skipped"
        )
