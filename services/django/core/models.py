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
    community_insights_opt_in = models.BooleanField(default=False, db_default=False)
    community_location_opt_in = models.BooleanField(default=False, db_default=False)
    community_country_code = models.CharField(
        max_length=8,
        null=True,
        blank=True,
        db_default=None,
    )
    community_region_code = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_default=None,
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", db_index=False)
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


class JournalContentFlag(models.Model):
    """Audit record for sensitive or inappropriate journal content."""

    id = models.AutoField(primary_key=True)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, db_column="journal_id")
    flag_type = models.CharField(max_length=32)
    severity = models.CharField(max_length=16)
    matched_terms = ArrayField(models.TextField(), default=list)
    analysis_summary = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_default=Now(),
    )

    class Meta:
        db_table = "journal_content_flags"
        indexes = [
            models.Index(fields=["journal"], name="idx_jcf_journal_id"),
            models.Index(fields=["flag_type"], name="idx_jcf_flag_type"),
        ]

    def __str__(self):
        return f"{self.flag_type} ({self.severity}) for Journal {self.journal.id}"


class JournalCommunityProjection(models.Model):
    """Privacy-safe journal attributes available to the community system."""

    journal = models.OneToOneField(
        Journal,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column="journal_id",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    eligible_for_community = models.BooleanField(default=False, db_default=False)
    entry_local_date = models.DateField(null=True, blank=True)
    primary_mood = models.CharField(max_length=32, null=True, blank=True)
    primary_sentiment = models.CharField(max_length=32, null=True, blank=True)
    theme_names = ArrayField(models.TextField(), default=list, blank=True)
    country_code = models.CharField(max_length=8, null=True, blank=True)
    region_code = models.CharField(max_length=32, null=True, blank=True)
    analysis_version = models.CharField(max_length=64, default="v1", db_default="v1")
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = "journal_community_projections"
        indexes = [
            models.Index(
                fields=["eligible_for_community", "entry_local_date"],
                name="idx_jcp_eligible_date",
            ),
            models.Index(
                fields=["region_code", "entry_local_date"],
                name="idx_jcp_region_date",
            ),
        ]

    def __str__(self):
        return f"Community projection for Journal {self.journal_id}"


class CommunityThemeRollup(models.Model):
    """Aggregated theme counts for community views."""

    id = models.AutoField(primary_key=True)
    bucket_date = models.DateField()
    time_grain = models.CharField(max_length=16)
    scope_type = models.CharField(max_length=16)
    scope_value = models.CharField(max_length=64)
    theme_name = models.CharField(max_length=100)
    entry_count = models.IntegerField()
    unique_user_count = models.IntegerField()
    rank = models.IntegerField()
    delta_vs_previous = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "community_theme_rollups"
        constraints = [
            models.UniqueConstraint(
                fields=["bucket_date", "time_grain", "scope_type", "scope_value", "theme_name"],
                name="uniq_community_theme_rollup",
            ),
        ]
        indexes = [
            models.Index(
                fields=["bucket_date", "time_grain", "scope_type", "scope_value"],
                name="idx_ctr_bucket_scope",
            ),
        ]

    def __str__(self):
        return f"{self.theme_name} on {self.bucket_date} ({self.scope_type}:{self.scope_value})"


class CommunityMoodRollup(models.Model):
    """Aggregated mood counts for community views."""

    id = models.AutoField(primary_key=True)
    bucket_date = models.DateField()
    time_grain = models.CharField(max_length=16)
    scope_type = models.CharField(max_length=16)
    scope_value = models.CharField(max_length=64)
    mood_name = models.CharField(max_length=100)
    entry_count = models.IntegerField()
    unique_user_count = models.IntegerField()
    rank = models.IntegerField()
    delta_vs_previous = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "community_mood_rollups"
        constraints = [
            models.UniqueConstraint(
                fields=["bucket_date", "time_grain", "scope_type", "scope_value", "mood_name"],
                name="uniq_community_mood_rollup",
            ),
        ]
        indexes = [
            models.Index(
                fields=["bucket_date", "time_grain", "scope_type", "scope_value"],
                name="idx_cmr_bucket_scope",
            ),
        ]

    def __str__(self):
        return f"{self.mood_name} on {self.bucket_date} ({self.scope_type}:{self.scope_value})"


class CommunitySummary(models.Model):
    """Stored privacy-safe summary for a community bucket."""

    id = models.AutoField(primary_key=True)
    bucket_date = models.DateField()
    time_grain = models.CharField(max_length=16)
    scope_type = models.CharField(max_length=16)
    scope_value = models.CharField(max_length=64)
    summary_text = models.TextField()
    source_theme_names = ArrayField(models.TextField(), default=list, blank=True)
    source_mood_names = ArrayField(models.TextField(), default=list, blank=True)
    generation_method = models.CharField(max_length=32, default="template", db_default="template")
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = "community_summaries"
        constraints = [
            models.UniqueConstraint(
                fields=["bucket_date", "time_grain", "scope_type", "scope_value"],
                name="uniq_community_summary",
            ),
        ]
        indexes = [
            models.Index(
                fields=["bucket_date", "time_grain", "scope_type", "scope_value"],
                name="idx_cs_bucket_scope",
            ),
        ]

    def __str__(self):
        return f"Summary on {self.bucket_date} ({self.scope_type}:{self.scope_value})"


class CommunityPromptSet(models.Model):
    """Stored prompt set for a community bucket."""

    id = models.AutoField(primary_key=True)
    bucket_date = models.DateField()
    time_grain = models.CharField(max_length=16)
    scope_type = models.CharField(max_length=16)
    scope_value = models.CharField(max_length=64)
    prompt_set_json = models.JSONField(default=list, blank=True)
    source_theme_names = ArrayField(models.TextField(), default=list, blank=True)
    source_mood_names = ArrayField(models.TextField(), default=list, blank=True)
    generation_method = models.CharField(max_length=32, default="template", db_default="template")
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = "community_prompt_sets"
        constraints = [
            models.UniqueConstraint(
                fields=["bucket_date", "time_grain", "scope_type", "scope_value"],
                name="uniq_community_prompt_set",
            ),
        ]
        indexes = [
            models.Index(
                fields=["bucket_date", "time_grain", "scope_type", "scope_value"],
                name="idx_cps_bucket_scope",
            ),
        ]

    def __str__(self):
        return f"Prompt set on {self.bucket_date} ({self.scope_type}:{self.scope_value})"


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


class JournalExport(models.Model):
    """Tracks async journal export jobs enqueued via River."""

    FORMAT_CHOICES = [
        ("csv", "CSV"),
        ("markdown", "Markdown"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("complete", "Complete"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=UUIDGenerateV4(),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="journal_exports",
    )
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default="csv")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    content = models.TextField(null=True, blank=True)
    error_msg = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "journal_exports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Export {self.id} ({self.format}) — {self.status}"


class StakeholderPrompt(models.Model):
    """Prompt authored by a stakeholder for use by LLM-driven Dagster jobs.

    The `application` field identifies what the prompt is used for
    (e.g. `sales_outreach`, `weekly_summary`) and is how Dagster jobs look up
    the right prompt. Each prompt belongs to a `stakeholder_group` (a Django
    `auth.Group`); admin access is scoped per-group so e.g. members of the
    `sales` group only see prompts owned by `sales`.
    """

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=UUIDGenerateV4(),
    )
    stakeholder_group = models.ForeignKey(
        "auth.Group",
        on_delete=models.PROTECT,
        related_name="stakeholder_prompts",
        db_column="stakeholder_group_id",
    )
    application = models.CharField(max_length=64, unique=True)
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "stakeholder_prompts"
        ordering = ["application"]

    def __str__(self):
        return f"{self.application} ({self.stakeholder_group.name})"


class StakeholderPromptResponse(models.Model):
    """Record of an LLM response for a given StakeholderPrompt."""

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=UUIDGenerateV4(),
    )
    stakeholder_prompt = models.ForeignKey(
        StakeholderPrompt,
        on_delete=models.CASCADE,
        db_column="stakeholder_prompt_id",
        related_name="responses",
    )
    model = models.CharField(max_length=64)
    response = models.TextField()
    run_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = "stakeholder_prompt_responses"
        ordering = ["-run_at"]
        indexes = [
            models.Index(
                fields=["stakeholder_prompt", "-run_at"],
                name="idx_spr_prompt_run_at",
            ),
        ]

    def __str__(self):
        return f"Response for {self.stakeholder_prompt.application} at {self.run_at}"


class IngestionWatermark(models.Model):
    """Durable cursor state for incremental Dagster ingestion jobs."""

    source_name = models.CharField(max_length=255, primary_key=True)
    watermark_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())
    last_run_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "ingestion_watermarks"
        ordering = ["source_name"]

    def __str__(self):
        return f"{self.source_name} through {self.watermark_at}"


class ExampleApiRecord(models.Model):
    """Landing table for the example modified_at-based incremental API feed."""

    source_id = models.CharField(max_length=255, primary_key=True)
    payload = models.JSONField(default=dict)
    modified_at = models.DateTimeField()
    ingested_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = "example_api_records"
        ordering = ["-modified_at", "source_id"]
        indexes = [
            models.Index(fields=["modified_at"], name="idx_example_api_modified_at"),
        ]

    def __str__(self):
        return f"Example API record {self.source_id}"


class ExampleApiUser(models.Model):
    """Landing table for the JSONPlaceholder users ingestion example."""

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    username = models.CharField(max_length=255)

    class Meta:
        db_table = "example_api_users"
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} ({self.email})"


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
