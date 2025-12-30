
from django.contrib.postgres.fields import ArrayField
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

    class Meta:
        db_table = "journals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "-created_at"], name="idx_journals_user_created"
            ),
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
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, db_column="journal_id"
    )
    topic_name = models.CharField(max_length=100)
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
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, db_column="journal_id"
    )
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
        return (
            f"{self.sentiment} ({self.confidence_level}) for Journal {self.journal.id}"
        )


class FeatureFlag(models.Model):
    """Feature flag model for managing feature toggles via Django admin."""

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=UUIDGenerateV4(),
    )
    flag_name = models.CharField(max_length=255, unique=True)
    enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "feature_flags"
        ordering = ["flag_name"]

    def __str__(self):
        status = "✓" if self.enabled else "✗"
        return f"{status} {self.flag_name}"


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
