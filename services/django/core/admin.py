from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

from .models import FeatureFlag


class LotusAdminSite(AdminSite):
    """Custom admin site for internal-only admin pages."""

    site_header = _("Lotus Admin")
    site_title = _("Lotus Admin Portal")
    index_title = _("Welcome to Lotus Administration")


# Create custom admin site instance
admin_site = LotusAdminSite(name="lotus_admin")


@admin.register(FeatureFlag, site=admin_site)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ("flag_name", "enabled", "created_at", "modified_at")
    list_filter = ("enabled", "created_at", "modified_at")
    search_fields = ("flag_name",)
    readonly_fields = ("id", "created_at", "modified_at")
    fieldsets = (
        (None, {"fields": ("id", "flag_name", "enabled")}),
        ("Timestamps", {"fields": ("created_at", "modified_at")}),
    )
    list_editable = ("enabled",)  # Allow quick editing of enabled status from list view
