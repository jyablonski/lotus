from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Mark initial migrations as applied (fake) since tables already exist"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "Marking migrations as applied (fake). "
                "This assumes tables already exist from bootstrap.sql"
            )
        )

        # Fake initial migrations
        try:
            call_command("migrate", "--fake-initial", verbosity=1)
            self.stdout.write(
                self.style.SUCCESS("Successfully marked migrations as applied")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
