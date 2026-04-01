from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import Func
from django.db.models.functions import Now


class UUIDGenerateV4(Func):
    """Database function wrapper for PostgreSQL's uuid_generate_v4()."""

    function = "uuid_generate_v4"
    template = "%(function)s()"


class User(models.Model):
    """User model matching the existing users table."""

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=UUIDGenerateV4(),
    )
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    salt = models.CharField(max_length=255, null=True, blank=True)
    oauth_provider = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(
        max_length=50,
        default="Consumer",
        db_default="Consumer",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_default=Now(),
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        db_default=Now(),
    )
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        db_default="UTC",
    )

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        """Check if user has Admin role."""
        return self.role == "Admin"


class Journal(models.Model):
    """Journal model matching the existing journals table."""

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    journal_text = models.TextField()
    mood_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_default=Now(),
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        db_default=Now(),
    )
    search_vector = SearchVectorField(null=True)

    class Meta:
        db_table = "journals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="idx_journals_user_created"),
            GinIndex(fields=["search_vector"], name="idx_journals_search_vector"),
        ]

    def __str__(self):
        return f"Journal {self.id} by {self.user.email}"


class JournalDetail(models.Model):
    """Journal detail model matching the existing journal_details table."""

    journal = models.OneToOneField(
        Journal, on_delete=models.CASCADE, primary_key=True, db_column="journal_id"
    )
    sentiment_score = models.FloatField(null=True, blank=True)
    mood_label = models.TextField(null=True, blank=True)
    keywords = ArrayField(models.TextField(), null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_default=Now(),
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        db_default=Now(),
    )

    class Meta:
        db_table = "journal_details"

    def __str__(self):
        return f"Details for Journal {self.journal.id}"


class JournalTopic(models.Model):
    """Journal topic model matching the existing journal_topics table."""

    id = models.AutoField(primary_key=True)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, db_column="journal_id")
    topic_name = models.CharField(max_length=100)
    subtopic_name = models.CharField(max_length=100, db_default=None, null=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=4)
    ml_model_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_default=Now(),
    )

    class Meta:
        db_table = "journal_topics"
        indexes = [
            models.Index(fields=["journal"], name="idx_journal_topics_journal_id"),
            models.Index(fields=["topic_name"], name="idx_journal_topics_topic_name"),
        ]

    def __str__(self):
        return f"{self.topic_name} ({self.confidence}) for Journal {self.journal.id}"


class JournalSentiment(models.Model):
    """Journal sentiment model matching the existing journal_sentiments table."""

    SENTIMENT_CHOICES = [
        ("positive", "Positive"),
        ("negative", "Negative"),
        ("neutral", "Neutral"),
        ("uncertain", "Uncertain"),
    ]

    CONFIDENCE_LEVEL_CHOICES = [
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]

    id = models.AutoField(primary_key=True)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, db_column="journal_id")
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES)
    confidence = models.DecimalField(max_digits=5, decimal_places=4)
    confidence_level = models.CharField(max_length=10, choices=CONFIDENCE_LEVEL_CHOICES)
    is_reliable = models.BooleanField(default=True)
    ml_model_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_default=Now(),
    )
    all_scores = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "journal_sentiments"
        unique_together = [["journal", "ml_model_version"]]

    def __str__(self):
        return f"{self.sentiment} ({self.confidence_level}) for Journal {self.journal.id}"


class JournalEmbedding(models.Model):
    """Stores vector embeddings for journal entries, used for semantic search via pgvector."""

    id = models.AutoField(primary_key=True)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, db_column="journal_id")
    embedding = models.TextField()  # Overridden to vector(384) via RunSQL in migration
    model_version = models.CharField(max_length=50, default="all-MiniLM-L6-v2")
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_default=Now(),
    )

    class Meta:
        db_table = "journal_embeddings"
        unique_together = [["journal", "model_version"]]

    def __str__(self):
        return f"Embedding ({self.model_version}) for Journal {self.journal.id}"


class ActiveMLModel(models.Model):
    """Model for tracking which ML models are currently enabled for the application."""

    id = models.AutoField(primary_key=True)
    ml_model = models.CharField(max_length=255, unique=True)
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "active_ml_models"
        ordering = ["ml_model"]

    def __str__(self):
        status = "✓" if self.is_enabled else "✗"
        return f"{status} {self.ml_model}"


class UserGameBalance(models.Model):
    """Per-user balance for the CSGODouble game."""

    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="game_balance",
    )
    balance = models.IntegerField(default=100)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_default=Now(),
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        db_default=Now(),
    )

    class Meta:
        db_table = "user_game_balances"

    def __str__(self):
        return f"{self.user.email} — ${self.balance}"


class UserGameBet(models.Model):
    """Records each bet placed by a user in the CSGODouble game."""

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="game_bets",
    )
    zone = models.CharField(max_length=10)  # '1-7', '0', '8-14'
    amount = models.IntegerField()
    roll_result = models.IntegerField()  # 0-14
    payout = models.IntegerField()  # 0 if lost
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_default=Now(),
    )

    class Meta:
        db_table = "user_game_bets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="idx_ugb_user_created",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} bet ${self.amount} on {self.zone} (roll={self.roll_result})"


class RuntimeConfig(models.Model):
    """Key-value configuration store for cross-service settings and runtime data.

    Stores arbitrary JSON data keyed by a unique string. Any service can read or write
    entries to share configuration, timestamps, state, or other data without requiring
    code changes.
    """

    SERVICE_CHOICES = [
        ("analyzer", "Analyzer"),
        ("backend", "Backend"),
        ("dagster", "Dagster"),
        ("dbt", "dbt"),
        ("django", "Django"),
        ("experiments", "Experiments"),
        ("frontend", "Frontend"),
    ]

    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField(default=dict)
    service = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    modified_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "runtime_config"
        ordering = ["key"]
        verbose_name = "runtime config"
        verbose_name_plural = "runtime config"

    def __str__(self):
        return self.key


class InvoiceSender(models.Model):
    """Reusable sender profile for invoices (the person sending the invoice)."""

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=UUIDGenerateV4(),
    )
    name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    modified_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "invoice_senders"
        ordering = ["name"]

    def __str__(self):
        return self.name


class InvoiceClient(models.Model):
    """Reusable client profile for invoices (the person/company being billed)."""

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=UUIDGenerateV4(),
    )
    name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, default="")
    attention = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    modified_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "invoice_clients"
        ordering = ["name"]

    def __str__(self):
        return self.name


class InvoicePaymentInfo(models.Model):
    """Reusable payment information for invoices."""

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=UUIDGenerateV4(),
    )
    check_payable_to = models.CharField(max_length=255)
    ach_account_number = models.CharField(max_length=50)
    ach_routing_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    modified_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "invoice_payment_info"
        verbose_name = "payment info"
        verbose_name_plural = "payment info"

    def __str__(self):
        return f"Payment info for {self.check_payable_to}"


class Invoice(models.Model):
    """Invoice header linking sender, client, and payment info."""

    TERMS_CHOICES = [
        ("Net 15", "Net 15"),
        ("Net 30", "Net 30"),
        ("Net 45", "Net 45"),
        ("Net 60", "Net 60"),
        ("Due on Receipt", "Due on Receipt"),
    ]

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=UUIDGenerateV4(),
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    sender = models.ForeignKey(InvoiceSender, on_delete=models.PROTECT, db_column="sender_id")
    client = models.ForeignKey(InvoiceClient, on_delete=models.PROTECT, db_column="client_id")
    payment_info = models.ForeignKey(
        InvoicePaymentInfo, on_delete=models.PROTECT, db_column="payment_info_id"
    )
    date = models.DateField()
    due_date = models.DateField()
    terms = models.CharField(max_length=50, choices=TERMS_CHOICES, default="Net 30")
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    modified_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "invoices"
        ordering = ["-date"]

    def __str__(self):
        return f"Invoice #{self.invoice_number} — {self.client.name}"

    @property
    def total(self):
        return sum(item.amount for item in self.line_items.all())


class InvoiceLineItem(models.Model):
    """Individual line item on an invoice."""

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=UUIDGenerateV4(),
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        db_column="invoice_id",
        related_name="line_items",
    )
    description = models.TextField()
    hours = models.DecimalField(max_digits=8, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = "invoice_line_items"
        ordering = ["id"]

    def __str__(self):
        return f"{self.description[:50]} — ${self.amount}"
