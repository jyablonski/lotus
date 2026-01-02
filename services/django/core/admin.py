import os

import requests
from django.contrib import admin
from django.contrib.auth.admin import (
    GroupAdmin as BaseGroupAdmin,
    UserAdmin as BaseUserAdmin,
)
from django.contrib.auth.models import Group, User
from django.contrib import messages
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
    change_list_template = "admin/core/featureflag/change_list.html"

    def get_urls(self):
        """Add custom URLs for this ModelAdmin"""
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "invalidate-cache/",
                self.admin_site.admin_view(self.invalidate_cache_view),
                name="core_featureflag_invalidate_cache",
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Override changelist view to add custom context"""
        extra_context = extra_context or {}
        from django.urls import reverse

        extra_context["invalidate_cache_url"] = reverse(
            "lotus_admin:core_featureflag_invalidate_cache"
        )
        return super().changelist_view(request, extra_context=extra_context)

    def invalidate_cache_view(self, request):
        """Custom admin view to invalidate analyzer cache"""
        from django.shortcuts import redirect
        from django.urls import reverse
        from django.http import JsonResponse

        # Handle AJAX requests
        if (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.content_type == "application/json"
        ):
            analyzer_url = os.environ.get("ANALYZER_BASE_URL", "http://analyzer:8083")
            endpoint = f"{analyzer_url}/v1/cache/invalidation"

            try:
                response = requests.post(endpoint, timeout=5)
                response.raise_for_status()
                response_data = response.json()
                messages.success(
                    request,
                    f"Successfully invalidated analyzer cache. Response: {response_data}",
                )
                return JsonResponse(
                    {"status": "success", "message": "Cache invalidated successfully"}
                )
            except requests.exceptions.RequestException as e:
                messages.error(
                    request,
                    f"Failed to invalidate analyzer cache: {str(e)}",
                )
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        # Handle regular requests (redirect)
        analyzer_url = os.environ.get("ANALYZER_BASE_URL", "http://analyzer:8083")
        endpoint = f"{analyzer_url}/v1/cache/invalidation"

        try:
            response = requests.post(endpoint, timeout=5)
            response.raise_for_status()
            response_data = response.json()
            messages.success(
                request,
                f"Successfully invalidated analyzer cache. Response: {response_data}",
            )
        except requests.exceptions.RequestException as e:
            messages.error(
                request,
                f"Failed to invalidate analyzer cache: {str(e)}",
            )

        # Redirect back to feature flag changelist
        return redirect(reverse("lotus_admin:core_featureflag_changelist"))


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
    list_editable = (
        "is_enabled",
    )  # Allow quick editing of enabled status from list view

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
