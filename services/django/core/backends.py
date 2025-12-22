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
            # Try to find user by email
            lotus_user = LotusUser.objects.get(email=username)

            # For OAuth users, we can't verify password here
            # In production, you'd want to integrate with your OAuth flow
            if lotus_user.password is None and lotus_user.oauth_provider:
                # OAuth user - create Django user if doesn't exist
                django_user, _ = DjangoUser.objects.get_or_create(
                    username=lotus_user.email, defaults={"email": lotus_user.email}
                )
                return django_user

            # For password-based users, verify password
            # Note: You'll need to implement password hashing verification
            # based on your password hashing scheme (salt + password)
            if password and lotus_user.password:
                # TODO: Implement password verification based on your hashing scheme
                # For now, this is a placeholder
                # You'll need to hash the password with the salt and compare
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
