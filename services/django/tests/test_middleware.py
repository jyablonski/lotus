from core.middleware import AdminOnlyMiddleware
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory
import pytest


@pytest.mark.django_db
class TestAdminOnlyMiddleware:
    def test_middleware_allows_login_page(self):
        def get_response(req):
            from django.http import HttpResponse

            return HttpResponse("OK")

        factory = RequestFactory()
        request = factory.get("/admin/login/")
        request.user = User.objects.create_user(username="test", email="test@test.com")

        middleware = AdminOnlyMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200

    def test_middleware_redirects_unauthenticated(self):
        def get_response(req):
            from django.http import HttpResponse

            return HttpResponse("OK")

        factory = RequestFactory()
        # Use a specific admin path that isn't in the skip list
        request = factory.get("/admin/core/featureflag/")
        request.user = AnonymousUser()

        middleware = AdminOnlyMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 302
        assert "/admin/login/" in response.url

    def test_middleware_denies_access_when_user_not_found(self):
        # When LotusUser doesn't exist, middleware should deny access
        def get_response(_req):
            from django.http import HttpResponse

            return HttpResponse("OK")

        django_user = User.objects.create_user(
            username="nonadmin@test.com",
            email="nonadmin@test.com",
        )

        factory = RequestFactory()
        # Use a specific admin path that isn't in the skip list
        request = factory.get("/admin/core/featureflag/")
        request.user = django_user
        # Add mock session since middleware calls logout() which requires session
        request.session = type("MockSession", (), {"flush": lambda self: None})()

        middleware = AdminOnlyMiddleware(get_response)
        response = middleware(request)

        # Should deny access since LotusUser with matching email doesn't exist
        assert response.status_code == 403

    def test_middleware_allows_unauthenticated_login_page(self):
        """Unauthenticated user should be allowed to access login page."""

        def get_response(req):
            from django.http import HttpResponse

            return HttpResponse("OK")

        factory = RequestFactory()
        request = factory.get("/admin/login/")
        request.user = AnonymousUser()

        middleware = AdminOnlyMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200

    def test_middleware_passes_through_non_admin_paths(self):
        """Middleware should not interfere with non-admin paths (bug fix)."""

        def get_response(req):
            from django.http import HttpResponse

            return HttpResponse("OK")

        factory = RequestFactory()
        # Non-admin paths should pass through without checks
        request = factory.get("/api/some-endpoint/")
        request.user = AnonymousUser()

        middleware = AdminOnlyMiddleware(get_response)
        response = middleware(request)

        # Should pass through without redirect or 403
        assert response.status_code == 200
        assert response.content == b"OK"
