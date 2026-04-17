from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import (
    GroupAdmin as BaseGroupAdmin,
    UserAdmin as BaseUserAdmin,
)
from django.contrib.auth.models import Group, User
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.sites import UnfoldAdminSite
from waffle.models import Flag, Sample, Switch

from .models import (
    ActiveMLModel,
    CommunityMoodRollup,
    CommunityPromptSet,
    CommunitySummary,
    CommunityThemeRollup,
    JournalCommunityProjection,
    JournalContentFlag,
    RuntimeConfig,
    StakeholderPrompt,
    StakeholderPromptResponse,
    User as LotusUser,
)


class LotusAdminSite(UnfoldAdminSite):
    """Custom admin site for internal-only admin pages."""

    site_header = _("Lotus Admin")
    site_title = _("Lotus Admin Portal")
    index_title = _("Welcome to Lotus Administration")

    def has_permission(self, request):
        """
        Override to use custom permission logic instead of is_staff.
        Allows users with Admin role or users in allowed groups.
        """
        from .middleware import _has_admin_access

        return _has_admin_access(request.user)


admin_site = LotusAdminSite(name="lotus_admin")

ACTIVE_ML_MODEL_ALLOWED_GROUPS = ("product", "ml_ops")

# Groups that may own and edit StakeholderPrompt rows. Members see and edit
# only the prompts that belong to their own group(s); Admin-role users bypass
# this restriction.
STAKEHOLDER_PROMPT_ALLOWED_GROUPS = ("sales", "product")


def _is_admin_role(user):
    """Return True if ``user`` has the Admin role in the LotusUser table."""
    if not user.is_authenticated:
        return False
    return LotusUser.objects.filter(
        email=user.email,
        role=getattr(settings, "ADMIN_ROLE_NAME", "Admin"),
    ).exists()


def _user_stakeholder_group_names(user) -> list[str]:
    """Names of allowed stakeholder groups the user belongs to."""
    if not user.is_authenticated:
        return []
    return list(
        user.groups.filter(name__in=STAKEHOLDER_PROMPT_ALLOWED_GROUPS).values_list(
            "name", flat=True
        )
    )


def _can_manage_stakeholder_prompts(user) -> bool:
    """Allow Admin-role users and members of any allowed stakeholder group."""
    return _is_admin_role(user) or bool(_user_stakeholder_group_names(user))


@admin.register(RuntimeConfig, site=admin_site)
class RuntimeConfigAdmin(ModelAdmin):
    list_display = ("key", "service", "value_preview", "description", "modified_at")
    list_filter = ("service", "created_at", "modified_at")
    search_fields = ("key", "description")
    readonly_fields = ("id", "created_at", "modified_at")
    fieldsets = (
        (None, {"fields": ("id", "key", "service", "value", "description")}),
        ("Timestamps", {"fields": ("created_at", "modified_at")}),
    )

    @admin.display(description="Value")
    def value_preview(self, obj):
        """Show a truncated preview of the JSON value in the list view."""
        import json

        text = json.dumps(obj.value)
        if len(text) > 80:
            return text[:80] + "..."
        return text


def has_ml_model_permission(user):
    """
    Check if user has permission to manage ML models.
    Allows users with the Admin role or members of the product/ml_ops groups.
    """
    if not user.is_authenticated:
        return False

    has_admin_role = LotusUser.objects.filter(
        email=user.email,
        role=getattr(settings, "ADMIN_ROLE_NAME", "Admin"),
    ).exists()
    is_in_allowed_group = user.groups.filter(name__in=ACTIVE_ML_MODEL_ALLOWED_GROUPS).exists()

    return has_admin_role or is_in_allowed_group


@admin.register(ActiveMLModel, site=admin_site)
class ActiveMLModelAdmin(ModelAdmin):
    list_display = ("ml_model", "is_enabled", "created_at", "modified_at")
    list_filter = ("is_enabled", "created_at", "modified_at")
    search_fields = ("ml_model",)
    readonly_fields = ("id", "created_at", "modified_at")
    fieldsets = (
        (None, {"fields": ("id", "ml_model", "is_enabled")}),
        ("Timestamps", {"fields": ("created_at", "modified_at")}),
    )
    list_editable = ("is_enabled",)

    def has_add_permission(self, request):
        """Only allow Admin role or product/ml_ops groups to add."""
        return has_ml_model_permission(request.user)

    def has_change_permission(self, request, obj=None):
        """Only allow Admin role or product/ml_ops groups to change."""
        return has_ml_model_permission(request.user)

    def has_delete_permission(self, request, obj=None):
        """Only allow Admin role or product/ml_ops groups to delete."""
        return has_ml_model_permission(request.user)

    def has_view_permission(self, request, obj=None):
        """Only allow Admin role or product/ml_ops groups to view."""
        return has_ml_model_permission(request.user)

    def has_module_permission(self, request):
        """Keep the model visible on the admin index for allowed users."""
        return has_ml_model_permission(request.user)


admin.site.unregister(User)
admin.site.unregister(Group)

# Waffle auto-registers on the default site; move its models to our custom one.
admin.site.unregister(Flag)
admin.site.unregister(Switch)
admin.site.unregister(Sample)


@admin.register(User, site=admin_site)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Use Unfold's forms so the auth UI matches the rest of the custom admin.
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group, site=admin_site)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(LotusUser, site=admin_site)
class LotusUserAdmin(ModelAdmin):
    list_display = (
        "email",
        "role",
        "community_insights_opt_in",
        "community_location_opt_in",
        "oauth_provider",
        "created_at",
        "modified_at",
    )
    list_filter = (
        "role",
        "community_insights_opt_in",
        "community_location_opt_in",
        "oauth_provider",
        "created_at",
        "modified_at",
    )
    search_fields = ("email",)
    readonly_fields = ("id", "created_at", "modified_at")
    fieldsets = (
        (None, {"fields": ("id", "email", "role", "timezone")}),
        ("Authentication", {"fields": ("password", "salt", "oauth_provider")}),
        (
            "Community",
            {
                "fields": (
                    "community_insights_opt_in",
                    "community_location_opt_in",
                    "community_country_code",
                    "community_region_code",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "modified_at")}),
    )


@admin.register(JournalContentFlag, site=admin_site)
class JournalContentFlagAdmin(ModelAdmin):
    list_display = ("journal", "flag_type", "severity", "created_at")
    list_filter = ("flag_type", "severity", "created_at")
    search_fields = ("journal__id", "analysis_summary", "matched_terms")
    readonly_fields = ("id", "created_at")
    fieldsets = (
        (None, {"fields": ("id", "journal", "flag_type", "severity")}),
        ("Analysis", {"fields": ("matched_terms", "analysis_summary")}),
        ("Timestamps", {"fields": ("created_at",)}),
    )


@admin.register(JournalCommunityProjection, site=admin_site)
class JournalCommunityProjectionAdmin(ModelAdmin):
    list_display = (
        "journal",
        "user",
        "eligible_for_community",
        "entry_local_date",
        "primary_mood",
        "primary_sentiment",
        "updated_at",
    )
    list_filter = (
        "eligible_for_community",
        "entry_local_date",
        "primary_mood",
        "primary_sentiment",
    )
    search_fields = ("journal__id", "user__email", "region_code", "country_code")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CommunityThemeRollup, site=admin_site)
class CommunityThemeRollupAdmin(ModelAdmin):
    list_display = (
        "bucket_date",
        "time_grain",
        "scope_type",
        "scope_value",
        "theme_name",
        "entry_count",
        "unique_user_count",
        "rank",
    )
    list_filter = ("bucket_date", "time_grain", "scope_type", "theme_name")
    search_fields = ("scope_value", "theme_name")
    readonly_fields = ("updated_at",)


@admin.register(CommunityMoodRollup, site=admin_site)
class CommunityMoodRollupAdmin(ModelAdmin):
    list_display = (
        "bucket_date",
        "time_grain",
        "scope_type",
        "scope_value",
        "mood_name",
        "entry_count",
        "unique_user_count",
        "rank",
    )
    list_filter = ("bucket_date", "time_grain", "scope_type", "mood_name")
    search_fields = ("scope_value", "mood_name")
    readonly_fields = ("updated_at",)


@admin.register(CommunitySummary, site=admin_site)
class CommunitySummaryAdmin(ModelAdmin):
    list_display = (
        "bucket_date",
        "time_grain",
        "scope_type",
        "scope_value",
        "summary_preview",
        "generation_method",
        "updated_at",
    )
    list_filter = ("bucket_date", "time_grain", "scope_type", "generation_method")
    search_fields = ("scope_value", "summary_text")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Summary")
    def summary_preview(self, obj):
        text = obj.summary_text
        if len(text) > 80:
            return text[:80] + "..."
        return text


@admin.register(CommunityPromptSet, site=admin_site)
class CommunityPromptSetAdmin(ModelAdmin):
    list_display = (
        "bucket_date",
        "time_grain",
        "scope_type",
        "scope_value",
        "generation_method",
        "updated_at",
    )
    list_filter = ("bucket_date", "time_grain", "scope_type", "generation_method")
    search_fields = ("scope_value",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(StakeholderPrompt, site=admin_site)
class StakeholderPromptAdmin(ModelAdmin):
    """Admin for StakeholderPrompt with strict per-group access control.

    Users with the Admin role see and manage every prompt. Members of
    ``STAKEHOLDER_PROMPT_ALLOWED_GROUPS`` only see and manage prompts that
    belong to their own group(s); the ``stakeholder_group`` dropdown is also
    filtered to prevent them from reassigning a prompt to another group.
    """

    list_display = (
        "application",
        "stakeholder_group",
        "prompt_preview",
        "updated_at",
    )
    list_filter = ("stakeholder_group", "created_at", "updated_at")
    search_fields = ("application", "stakeholder_group__name", "prompt")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("id", "application", "stakeholder_group", "prompt")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Prompt")
    def prompt_preview(self, obj):
        text = obj.prompt
        if len(text) > 80:
            return text[:80] + "..."
        return text

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("stakeholder_group")
        if _is_admin_role(request.user):
            return qs
        return qs.filter(stakeholder_group__name__in=_user_stakeholder_group_names(request.user))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "stakeholder_group" and not _is_admin_role(request.user):
            kwargs["queryset"] = Group.objects.filter(
                name__in=_user_stakeholder_group_names(request.user)
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_module_permission(self, request):
        return _can_manage_stakeholder_prompts(request.user)

    def has_view_permission(self, request, obj=None):
        if not _can_manage_stakeholder_prompts(request.user):
            return False
        if obj is None or _is_admin_role(request.user):
            return True
        return obj.stakeholder_group.name in _user_stakeholder_group_names(request.user)

    def has_add_permission(self, request):
        return _can_manage_stakeholder_prompts(request.user)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)


@admin.register(StakeholderPromptResponse, site=admin_site)
class StakeholderPromptResponseAdmin(ModelAdmin):
    """Read-only history view of LLM responses, scoped to user's group(s).

    Admins see everything; group members only see responses tied to prompts in
    their own group(s). Rows are created by Dagster jobs, not through the
    admin, so add/change/delete are disabled for everyone.
    """

    list_display = (
        "stakeholder_prompt",
        "model",
        "response_preview",
        "run_at",
    )
    list_filter = ("model", "run_at", "stakeholder_prompt__stakeholder_group")
    search_fields = (
        "stakeholder_prompt__application",
        "stakeholder_prompt__stakeholder_group__name",
        "response",
    )
    readonly_fields = ("id", "stakeholder_prompt", "model", "response", "run_at")
    fieldsets = (
        (None, {"fields": ("id", "stakeholder_prompt", "model", "response")}),
        ("Timestamps", {"fields": ("run_at",)}),
    )

    @admin.display(description="Response")
    def response_preview(self, obj):
        text = obj.response
        if len(text) > 80:
            return text[:80] + "..."
        return text

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("stakeholder_prompt__stakeholder_group")
        if _is_admin_role(request.user):
            return qs
        return qs.filter(
            stakeholder_prompt__stakeholder_group__name__in=_user_stakeholder_group_names(
                request.user
            )
        )

    def has_module_permission(self, request):
        return _can_manage_stakeholder_prompts(request.user)

    def has_view_permission(self, request, obj=None):
        if not _can_manage_stakeholder_prompts(request.user):
            return False
        if obj is None or _is_admin_role(request.user):
            return True
        return obj.stakeholder_prompt.stakeholder_group.name in (
            _user_stakeholder_group_names(request.user)
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Flag, site=admin_site)
class WaffleFlagAdmin(ModelAdmin):
    list_display = ("name", "everyone", "superusers", "staff", "note", "created", "modified")
    list_filter = ("everyone", "superusers", "staff")
    search_fields = ("name", "note")
    filter_horizontal = ("groups", "users")


@admin.register(Switch, site=admin_site)
class WaffleSwitchAdmin(ModelAdmin):
    list_display = ("name", "active", "note", "created", "modified")
    list_filter = ("active",)
    search_fields = ("name", "note")


@admin.register(Sample, site=admin_site)
class WaffleSampleAdmin(ModelAdmin):
    list_display = ("name", "percent", "note", "created", "modified")
    search_fields = ("name", "note")
