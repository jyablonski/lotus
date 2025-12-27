from django.conf import settings
from django.contrib.auth import logout
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def _has_admin_access(user):
    """
    Check if user has admin access (cached).
    Allows users with Admin role or users in allowed groups.
    """
    if not user.is_authenticated:
        return False

    # Cache key based on user ID and email
    cache_key = f"admin_access_{user.id}_{user.email}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        from .models import User as LotusUser

        # Check if user has Admin role
        db_user = LotusUser.objects.filter(email=user.email).first()
        has_admin_role = db_user and db_user.role == settings.ADMIN_ROLE_NAME

        # Check if user is in allowed groups (configurable via settings)
        allowed_groups = getattr(settings, "ADMIN_ALLOWED_GROUPS", ["product_manager"])
        is_in_allowed_group = user.groups.filter(name__in=allowed_groups).exists()

        has_access = has_admin_role or is_in_allowed_group

        # Cache for 5 minutes to reduce database queries
        cache.set(cache_key, has_access, 300)
        return has_access
    except Exception:
        # On error, deny access for safety
        return False


class AdminOnlyMiddleware:
    """
    Middleware that ensures only admin users can access admin pages.
    Checks the user's role from the users table and allowed groups.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply to admin URLs (fixed: removed the "/" check that matched everything)
        if not request.path.startswith("/admin/"):
            response = self.get_response(request)
            return response

        # Skip authentication check for login/logout pages
        if request.path in ["/admin/login/", "/admin/logout/", "/admin/"]:
            response = self.get_response(request)
            return response

        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Allow access to login page
            if request.path == "/admin/login/":
                response = self.get_response(request)
                return response
            # Redirect to login for other admin pages
            return redirect("/admin/login/?next=" + request.path)

        # Check if user has admin access (cached)
        if _has_admin_access(request.user):
            # User has access, allow
            response = self.get_response(request)
            return response
        else:
            # User does not have access, deny
            logout(request)
            return HttpResponseForbidden(
                "<h1>403 Forbidden</h1><p>Admin or Product Manager access required. Only users with Admin role or Product Manager group membership can access this interface.</p>"
            )
