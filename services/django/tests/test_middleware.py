import pytest
from core.middleware import AdminOnlyMiddleware
from core.models import User as LotusUser
from django.contrib.auth.models import User
from django.test import RequestFactory


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

    def test_middleware_allows_admin_user(self):
        lotus_user = LotusUser.objects.create(  # noqa: F841
            email="admin@test.com",
            role="Admin",
            timezone="UTC",
        )
        django_user = User.objects.create_user(
            username="admin@test.com",
            email="admin@test.com",
        )

        factory = RequestFactory()
        request = factory.get("/admin/")
        request.user = django_user

        def get_response(req):
            from django.http import HttpResponse

            return HttpResponse("OK")

        middleware = AdminOnlyMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200

    def test_middleware_denies_non_admin_user(self):
        def get_response(req):
            from django.http import HttpResponse

            return HttpResponse("OK")

        lotus_user = LotusUser.objects.create(  # noqa: F841
            email="user@test.com",
            role="Consumer",
            timezone="UTC",
        )
        django_user = User.objects.create_user(
            username="user@test.com",
            email="user@test.com",
        )

        factory = RequestFactory()
        request = factory.get("/admin/")
        request.user = django_user

        middleware = AdminOnlyMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 403
