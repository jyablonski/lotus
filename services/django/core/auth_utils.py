from django.conf import settings


def has_admin_role(lotus_user):
    """Return whether the Lotus user should be treated as an admin."""
    return bool(lotus_user and lotus_user.role == getattr(settings, "ADMIN_ROLE_NAME", "Admin"))


def is_in_allowed_admin_group(django_user):
    """Return whether the Django user belongs to an admin-enabled stakeholder group."""
    allowed_groups = getattr(settings, "ADMIN_ALLOWED_GROUPS", ["product_manager"])
    return django_user.groups.filter(name__in=allowed_groups).exists()


def desired_django_access_flags(*, django_user, lotus_user):
    """
    Compute the Django auth flags implied by Lotus role and stakeholder groups.

    `is_superuser` stays reserved for the Lotus admin role.
    `is_staff` can also be granted through the configured admin-allowed groups.
    """
    is_superuser = has_admin_role(lotus_user)
    is_staff = is_superuser or is_in_allowed_admin_group(django_user)
    return is_staff, is_superuser
