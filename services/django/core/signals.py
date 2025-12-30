"""
Signals to sync Django Users with Lotus Users.
Keeps Django auth.User in sync with core.User for admin access.
"""

from django.contrib.auth.models import User as DjangoUser
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import User as LotusUser


@receiver(post_save, sender=LotusUser)
def sync_django_user(sender, instance, created, **kwargs):
    """
    Sync Django User when Lotus User is created or updated.
    Creates/updates Django User to match Lotus User.
    - Admin role users get is_staff=True and is_superuser=True
    - Other users get basic Django User (created for consistency)
    """
    from django.conf import settings

    django_user, django_created = DjangoUser.objects.get_or_create(
        username=instance.email,
        defaults={"email": instance.email},
    )

    # Update email if it changed
    if django_user.email != instance.email:
        django_user.email = instance.email
        django_user.save()

    # Set admin privileges based on role
    is_admin = instance.role == getattr(settings, "ADMIN_ROLE_NAME", "Admin")
    django_user.is_staff = is_admin
    django_user.is_superuser = is_admin
    django_user.save()


@receiver(post_delete, sender=LotusUser)
def delete_django_user(sender, instance, **kwargs):
    """
    Delete Django User when Lotus User is deleted.
    """
    try:
        django_user = DjangoUser.objects.get(username=instance.email)
        django_user.delete()
    except DjangoUser.DoesNotExist:
        pass  # Django User doesn't exist, nothing to delete
