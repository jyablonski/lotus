from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


class AdminOnlyMiddleware:
    """
    Middleware that ensures only admin users can access admin pages.
    Checks the user's role from the users table.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply to admin URLs
        if request.path.startswith("/admin/") or request.path.startswith("/"):
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

            # Check if user has admin role
            # We need to check the User model from our database
            try:
                from .models import User

                # Try to get the user from our User model
                # Django's auth user email should match our User model email
                db_user = User.objects.filter(email=request.user.email).first()

                if db_user and db_user.role == settings.ADMIN_ROLE_NAME:
                    # User is admin, allow access
                    response = self.get_response(request)
                    return response
                else:
                    # User is not admin, deny access
                    logout(request)
                    return HttpResponseForbidden(
                        "<h1>403 Forbidden</h1><p>Admin access required. Only users with Admin role can access this interface.</p>"
                    )
            except Exception:
                # If there's an error checking, deny access for safety
                logout(request)
                return HttpResponseForbidden(
                    "<h1>403 Forbidden</h1><p>Error verifying admin access.</p>"
                )

        response = self.get_response(request)
        return response
