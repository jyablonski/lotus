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

    cache_key = f"admin_access_{user.id}_{user.email}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        from .models import User as LotusUser

        db_user = LotusUser.objects.filter(email=user.email).first()
        has_admin_role = db_user and db_user.role == settings.ADMIN_ROLE_NAME

        allowed_groups = getattr(settings, "ADMIN_ALLOWED_GROUPS", ["product_manager"])
        is_in_allowed_group = user.groups.filter(name__in=allowed_groups).exists()

        has_access = has_admin_role or is_in_allowed_group

        cache.set(cache_key, has_access, 300)
        return has_access
    except Exception:
        # Fail closed so a lookup error cannot grant admin access.
        return False


class AdminOnlyMiddleware:
    """
    Middleware that ensures only admin users can access admin pages.
    Checks the user's role from the users table and allowed groups.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # The custom admin site is mounted at /core/; the stock Django admin at /admin/.
        is_admin_path = request.path.startswith("/admin/") or request.path.startswith("/core/")

        if not is_admin_path:
            response = self.get_response(request)
            return response

        login_paths = ["/admin/login/", "/admin/logout/", "/admin/", "/login/", "/logout/", "/"]
        if request.path in login_paths:
            response = self.get_response(request)
            return response

        if not request.user.is_authenticated:
            if request.path in ["/admin/login/", "/login/"]:
                response = self.get_response(request)
                return response
            login_url = "/login/" if request.path.startswith("/core/") else "/admin/login/"
            return redirect(f"{login_url}?next={request.path}")

        if _has_admin_access(request.user):
            response = self.get_response(request)
            return response
        else:
            logout(request)
            return HttpResponseForbidden(
                "<h1>403 Forbidden</h1><p>Admin or Product Manager access required. Only users with Admin role or Product Manager group membership can access this interface.</p>"
            )
