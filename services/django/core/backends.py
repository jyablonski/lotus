from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User as DjangoUser

from .models import User as LotusUser


class LotusUserBackend(BaseBackend):
    """
    Authentication backend that authenticates against the Lotus users table.
    Creates Django User objects on the fly for admin interface compatibility.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user against Lotus users table.
        For OAuth users (password is None), we'll need a different approach.
        """
        if username is None:
            username = kwargs.get("email")

        try:
            lotus_user = LotusUser.objects.get(email=username)

            # OAuth users have no local password; trust the OAuth flow upstream
            # and mirror them into Django auth so the admin session works.
            if lotus_user.password is None and lotus_user.oauth_provider:
                django_user, _ = DjangoUser.objects.get_or_create(
                    username=lotus_user.email, defaults={"email": lotus_user.email}
                )
                return django_user

            # TODO: verify password against the project's salt+hash scheme before
            # returning a Django user. Currently accepts any non-empty password.
            if password and lotus_user.password:
                django_user, _ = DjangoUser.objects.get_or_create(
                    username=lotus_user.email, defaults={"email": lotus_user.email}
                )
                return django_user

        except LotusUser.DoesNotExist:
            return None

        return None

    def get_user(self, user_id):
        try:
            django_user = DjangoUser.objects.get(pk=user_id)
            return django_user
        except DjangoUser.DoesNotExist:
            return None
