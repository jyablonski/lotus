import pytest
from core.middleware import AdminOnlyMiddleware
from django.contrib.auth.models import User
from django.test import RequestFactory


# NOTE: The core models (User, Journal, etc.) have managed=False, which means Django
# won't create their tables in the test database. This makes it difficult to test
# middleware that queries these models (like AdminOnlyMiddleware checking User.role).
# Full integration tests would require manually creating these tables in test setup,
# which we're deferring. For now, we test basic middleware behavior without the
# LotusUser lookup.
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
        request = factory.get("/admin/")
        request.user = User()

        middleware = AdminOnlyMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 302
        assert "/admin/login/" in response.url

    def test_middleware_denies_access_when_user_not_found(self):
        # When LotusUser doesn't exist (which will happen in tests since managed=False),
        # middleware should deny access
        def get_response(req):
            from django.http import HttpResponse

            return HttpResponse("OK")

        django_user = User.objects.create_user(
            username="user@test.com",
            email="user@test.com",
        )

        factory = RequestFactory()
        request = factory.get("/admin/")
        request.user = django_user

        middleware = AdminOnlyMiddleware(get_response)
        response = middleware(request)

        # Should deny access since LotusUser lookup will fail (table doesn't exist in test DB)
        assert response.status_code == 403
