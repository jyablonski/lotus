from datetime import timedelta
import os
from random import Random
import time

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User as DjangoUser
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
import requests

from core.models import (
    Journal,
    User as LotusUser,
)

TIMEZONES = [
    "UTC",
    "America/Los_Angeles",
    "America/New_York",
    "Europe/London",
    "Europe/Berlin",
    "Asia/Tokyo",
    "Australia/Sydney",
]

LOW_MOOD_OPENERS = [
    "Today felt heavier than I expected.",
    "I had a hard time staying grounded today.",
    "A lot of small frustrations stacked up today.",
    "I felt stretched thin for most of the day.",
]

MID_MOOD_OPENERS = [
    "Today felt pretty balanced overall.",
    "It was an ordinary day with a few bright spots.",
    "I moved through the day at a steady pace.",
    "Today had a mix of pressure and progress.",
]

HIGH_MOOD_OPENERS = [
    "Today felt energizing and clear.",
    "I ended the day feeling proud of how things went.",
    "There was a good sense of momentum today.",
    "I felt noticeably lighter and more optimistic today.",
]

FOCUS_AREAS = [
    "work priorities",
    "a conversation with a friend",
    "family routines",
    "exercise and recovery",
    "sleep and rest",
    "therapy homework",
    "a creative project",
    "planning for the week",
    "household tasks",
    "money stress",
    "team collaboration",
    "learning something new",
]

REFLECTIONS = [
    "I kept noticing how much my mindset shaped the rest of the day.",
    "Writing this down helps me see the pattern more clearly.",
    "I want to remember this moment because it says a lot about what I need.",
    "It reminded me that small habits matter more than dramatic changes.",
    "I could feel my energy shift once I slowed down and paid attention.",
    "The best part was realizing I handled it better than I would have a few months ago.",
]

LOW_MOOD_CLOSERS = [
    "Tomorrow I want to keep things simple and give myself more room to breathe.",
    "My goal for tomorrow is to ask for help earlier instead of pushing through alone.",
    "I need a calmer start tomorrow and a more realistic plan.",
]

MID_MOOD_CLOSERS = [
    "I think a little consistency tomorrow would go a long way.",
    "Nothing dramatic happened, but the day still gave me something useful to notice.",
    "I want to carry the steady parts of today into tomorrow.",
]

HIGH_MOOD_CLOSERS = [
    "I want to build on this momentum while it still feels natural.",
    "Days like this make me trust my routines a little more.",
    "I hope I can hold onto this sense of perspective tomorrow too.",
]


class Command(BaseCommand):
    help = "Generate example Lotus users and journal entries for local/demo environments"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=100,
            help="Number of Lotus users to create (default: 100)",
        )
        parser.add_argument(
            "--journals",
            type=int,
            default=10000,
            help="Number of journal entries to create (default: 10000)",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for deterministic output (default: 42)",
        )
        parser.add_argument(
            "--email-prefix",
            type=str,
            default="example-user",
            help="Prefix used for generated emails before the numeric suffix",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Batch size for user inserts and progress logging (default: 1000)",
        )
        parser.add_argument(
            "--reset-prefix",
            action="store_true",
            help="Delete previously generated users and journals for this prefix before seeding",
        )
        parser.add_argument(
            "--backend-base-url",
            type=str,
            default=os.environ.get("BACKEND_BASE_URL", "http://localhost:8080"),
            help="Backend base URL used for journal creation (default: http://localhost:8080)",
        )
        parser.add_argument(
            "--backend-api-key",
            type=str,
            default=os.environ.get("BACKEND_API_KEY", ""),
            help="Backend API key used as Authorization Bearer token",
        )
        parser.add_argument(
            "--request-timeout",
            type=float,
            default=10.0,
            help="Timeout in seconds for each backend journal create request (default: 10)",
        )
        parser.add_argument(
            "--requests-per-second",
            type=float,
            default=10.0,
            help="Max journal create requests per second sent to the backend (default: 10)",
        )
        parser.add_argument(
            "--max-retries",
            type=int,
            default=6,
            help="Max retries for a journal create when the backend rate limits (default: 6)",
        )

    def handle(self, *args, **options):
        user_count = options["users"]
        journal_count = options["journals"]
        seed = options["seed"]
        email_prefix = options["email_prefix"].strip()
        batch_size = options["batch_size"]
        reset_prefix = options["reset_prefix"]
        backend_base_url = options["backend_base_url"].strip().rstrip("/")
        backend_api_key = options["backend_api_key"].strip()
        request_timeout = options["request_timeout"]
        requests_per_second = options["requests_per_second"]
        max_retries = options["max_retries"]

        if user_count < 1:
            raise CommandError("--users must be greater than 0")
        if journal_count < 1:
            raise CommandError("--journals must be greater than 0")
        if batch_size < 1:
            raise CommandError("--batch-size must be greater than 0")
        if not email_prefix:
            raise CommandError("--email-prefix cannot be blank")
        if not backend_base_url:
            raise CommandError("--backend-base-url cannot be blank")
        if not backend_api_key:
            raise CommandError("--backend-api-key cannot be blank and BACKEND_API_KEY must be set")
        if request_timeout <= 0:
            raise CommandError("--request-timeout must be greater than 0")
        if requests_per_second <= 0:
            raise CommandError("--requests-per-second must be greater than 0")
        if max_retries < 1:
            raise CommandError("--max-retries must be greater than 0")

        rng = Random(seed)
        now = timezone.now()
        generated_prefix = f"{email_prefix}-"
        target_emails = [
            f"{generated_prefix}{index:04d}@lotus.local" for index in range(1, user_count + 1)
        ]

        with transaction.atomic():
            if reset_prefix:
                deleted_journal_count, _ = Journal.objects.filter(
                    user__email__startswith=generated_prefix
                ).delete()
                deleted_user_count, _ = LotusUser.objects.filter(
                    email__startswith=generated_prefix
                ).delete()
                DjangoUser.objects.filter(username__startswith=generated_prefix).delete()

                self.stdout.write(
                    self.style.WARNING(
                        "Cleared existing generated data for prefix "
                        f"'{generated_prefix}' "
                        f"({deleted_user_count} users, {deleted_journal_count} journals)"
                    )
                )

            existing_emails = set(
                LotusUser.objects.filter(email__in=target_emails).values_list("email", flat=True)
            )
            lotus_users_to_create = []

            for index, email in enumerate(target_emails, start=1):
                if email in existing_emails:
                    continue

                created_at = now - timedelta(
                    days=rng.randint(0, 365),
                    hours=rng.randint(0, 23),
                    minutes=rng.randint(0, 59),
                )
                timezone_name = TIMEZONES[(index - 1) % len(TIMEZONES)]

                lotus_users_to_create.append(
                    LotusUser(
                        email=email,
                        role="Consumer",
                        timezone=timezone_name,
                        created_at=created_at,
                        modified_at=created_at,
                    )
                )
            if lotus_users_to_create:
                LotusUser.objects.bulk_create(lotus_users_to_create, batch_size=batch_size)

            lotus_users = list(LotusUser.objects.filter(email__in=target_emails).order_by("email"))
            existing_django_usernames = set(
                DjangoUser.objects.filter(username__in=target_emails).values_list(
                    "username",
                    flat=True,
                )
            )
            missing_django_users = [
                DjangoUser(
                    username=lotus_user.email,
                    email=lotus_user.email,
                    password=make_password(None),
                    is_staff=False,
                    is_superuser=False,
                    date_joined=lotus_user.created_at,
                )
                for lotus_user in lotus_users
                if lotus_user.email not in existing_django_usernames
            ]
            if missing_django_users:
                DjangoUser.objects.bulk_create(missing_django_users, batch_size=batch_size)

        self.stdout.write(
            f"Creating {journal_count} journals through backend endpoint "
            f"{backend_base_url}/v1/journals at up to {requests_per_second:g} req/s"
        )

        min_interval_seconds = 1.0 / requests_per_second
        next_request_at = time.monotonic()
        with requests.Session() as session:
            for journal_index in range(1, journal_count + 1):
                now_monotonic = time.monotonic()
                if next_request_at > now_monotonic:
                    time.sleep(next_request_at - now_monotonic)
                next_request_at = max(next_request_at + min_interval_seconds, time.monotonic())

                owner = lotus_users[rng.randrange(len(lotus_users))]
                created_at = now - timedelta(
                    days=rng.randint(0, 365),
                    hours=rng.randint(0, 23),
                    minutes=rng.randint(0, 59),
                )
                modified_at = min(now, created_at + timedelta(minutes=rng.randint(0, 180)))
                mood_score = min(10, max(1, round(rng.gauss(6, 2))))
                journal_text = self._build_journal_text(
                    rng=rng,
                    mood_score=mood_score,
                    journal_index=journal_index,
                )

                journal_id = self._create_journal_via_backend(
                    session=session,
                    backend_base_url=backend_base_url,
                    backend_api_key=backend_api_key,
                    user_id=str(owner.id),
                    journal_text=journal_text,
                    mood_score=mood_score,
                    timeout=request_timeout,
                    max_retries=max_retries,
                )
                Journal.objects.filter(id=journal_id).update(
                    created_at=created_at,
                    modified_at=modified_at,
                )

                if journal_index % batch_size == 0 or journal_index == journal_count:
                    self.stdout.write(
                        f"Created {journal_index}/{journal_count} journals via backend"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Generated {user_count} users and {journal_count} journals "
                f"for prefix '{generated_prefix}' using seed {seed} "
                f"via backend {backend_base_url}."
            )
        )

    def _create_journal_via_backend(
        self,
        *,
        session: requests.Session,
        backend_base_url: str,
        backend_api_key: str,
        user_id: str,
        journal_text: str,
        mood_score: int,
        timeout: float,
        max_retries: int,
    ) -> int:
        for attempt in range(1, max_retries + 1):
            try:
                response = session.post(
                    f"{backend_base_url}/v1/journals",
                    json={
                        "user_id": user_id,
                        "journal_text": journal_text,
                        "user_mood": str(mood_score),
                    },
                    headers={
                        "Authorization": f"Bearer {backend_api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=timeout,
                )
            except requests.RequestException as exc:
                raise CommandError(f"backend journal creation request failed: {exc}") from exc

            if response.status_code == 429 and attempt < max_retries:
                retry_after = self._retry_delay_seconds(response, attempt)
                self.stdout.write(
                    self.style.WARNING(
                        "Backend rate limited journal creation; "
                        f"sleeping {retry_after:.2f}s before retry {attempt + 1}/{max_retries}"
                    )
                )
                time.sleep(retry_after)
                continue

            if not response.ok:
                detail = response.text.strip()
                if detail:
                    raise CommandError(
                        f"backend journal creation failed with status {response.status_code}: {detail}"
                    )
                raise CommandError(
                    f"backend journal creation failed with status {response.status_code}"
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise CommandError("backend journal creation returned invalid JSON") from exc

            journal_id = payload.get("journalId") or payload.get("journal_id")
            if journal_id is None:
                raise CommandError("backend journal creation response did not include journalId")

            try:
                return int(journal_id)
            except (TypeError, ValueError) as exc:
                raise CommandError(
                    f"backend journal creation returned invalid journalId: {journal_id!r}"
                ) from exc

        raise CommandError("backend journal creation failed after exhausting retries")

    def _retry_delay_seconds(self, response: requests.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After", "").strip()
        try:
            if retry_after:
                return max(float(retry_after), 0.25)
        except ValueError:
            pass
        return min(0.5 * (2 ** (attempt - 1)), 8.0)

    def _build_journal_text(self, *, rng: Random, mood_score: int, journal_index: int) -> str:
        opener_pool, closer_pool = self._mood_pools(mood_score)
        opener = rng.choice(opener_pool)
        focus_area = rng.choice(FOCUS_AREAS)
        reflection = rng.choice(REFLECTIONS)
        closer = rng.choice(closer_pool)

        return (
            f"Entry {journal_index}: {opener} "
            f"I spent time thinking about {focus_area}. "
            f"{reflection} {closer}"
        )

    def _mood_pools(self, mood_score: int) -> tuple[list[str], list[str]]:
        if mood_score <= 4:
            return LOW_MOOD_OPENERS, LOW_MOOD_CLOSERS
        if mood_score <= 7:
            return MID_MOOD_OPENERS, MID_MOOD_CLOSERS
        return HIGH_MOOD_OPENERS, HIGH_MOOD_CLOSERS
