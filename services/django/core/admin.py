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

from .models import (
    ActiveMLModel,
    FeatureFlag,
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


@admin.register(FeatureFlag, site=admin_site)
class FeatureFlagAdmin(ModelAdmin):
    list_display = ("flag_name", "enabled", "created_at", "modified_at")
    list_filter = ("enabled", "created_at", "modified_at")
    search_fields = ("flag_name",)
    readonly_fields = ("id", "created_at", "modified_at")
    fieldsets = (
        (None, {"fields": ("id", "flag_name", "enabled")}),
        ("Timestamps", {"fields": ("created_at", "modified_at")}),
    )
    list_editable = ("enabled",)  # Allow quick editing of enabled status from list view


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
        """Only allow Admin role or allowed groups (product_manager, ml_engineer) to add."""
        return has_ml_model_permission(request.user)

    def has_change_permission(self, request, obj=None):
        """Only allow Admin role or allowed groups (product_manager, ml_engineer) to change."""
        return has_ml_model_permission(request.user)

    def has_delete_permission(self, request, obj=None):
        """Only allow Admin role or allowed groups (product_manager, ml_engineer) to delete."""
        return has_ml_model_permission(request.user)

    def has_view_permission(self, request, obj=None):
        """Only allow Admin role or allowed groups (product_manager, ml_engineer) to view."""
        return has_ml_model_permission(request.user)


# Unregister User and Group from default admin site
admin.site.unregister(User)
admin.site.unregister(Group)


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
    list_display = ("email", "role", "oauth_provider", "created_at", "modified_at")
    list_filter = ("role", "oauth_provider", "created_at", "modified_at")
    search_fields = ("email",)
    readonly_fields = ("id", "created_at", "modified_at")
    fieldsets = (
        (None, {"fields": ("id", "email", "role", "timezone")}),
        ("Authentication", {"fields": ("password", "salt", "oauth_provider")}),
        ("Timestamps", {"fields": ("created_at", "modified_at")}),
    )
