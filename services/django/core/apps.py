from django.apps import AppConfig
from waffle.apps import WaffleConfig as BaseWaffleConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """Import signals when app is ready."""
        import core.signals  # noqa: F401


class WaffleConfig(BaseWaffleConfig):
    """Override waffle's AppConfig to customize the admin section name."""

    verbose_name = "Feature Flags"
