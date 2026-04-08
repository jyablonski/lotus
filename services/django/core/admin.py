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


# Create custom admin site instance
admin_site = LotusAdminSite(name="lotus_admin")


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
    Allows users with Admin role or users in allowed groups.
    Uses the same logic as middleware for consistency.
    """
    from .middleware import _has_admin_access

    return _has_admin_access(user)


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
    list_editable = ("is_enabled",)  # Allow quick editing of enabled status from list view

    def has_add_permission(self, request):
        """Only allow Admin role or allowed groups (product, ml_ops, infrastructure, engineering) to add."""
        return has_ml_model_permission(request.user)

    def has_change_permission(self, request, obj=None):
        """Only allow Admin role or allowed groups (product, ml_ops, infrastructure, engineering) to change."""
        return has_ml_model_permission(request.user)

    def has_delete_permission(self, request, obj=None):
        """Only allow Admin role or allowed groups (product, ml_ops, infrastructure, engineering) to delete."""
        return has_ml_model_permission(request.user)

    def has_view_permission(self, request, obj=None):
        """Only allow Admin role or allowed groups (product, ml_ops, infrastructure, engineering) to view."""
        return has_ml_model_permission(request.user)


# Unregister User and Group from default admin site
admin.site.unregister(User)
admin.site.unregister(Group)

# Unregister Waffle models from default admin site (they auto-register there)
admin.site.unregister(Flag)
admin.site.unregister(Switch)
admin.site.unregister(Sample)


# Register User and Group with custom admin site
@admin.register(User, site=admin_site)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms` for proper Unfold styling
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


# Register Waffle models with custom admin site
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
