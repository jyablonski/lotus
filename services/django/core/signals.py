"""
Signals to sync Django Users with Lotus Users.
Keeps Django auth.User in sync with core.User for admin access.
"""

from django.contrib.auth.models import User as DjangoUser
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from .models import User as LotusUser


# Store old email before save to handle email updates
_old_email_cache = {}


@receiver(pre_save, sender=LotusUser)
def store_old_email(sender, instance, **kwargs):
    """Store old email before save to handle email updates."""
    if instance.pk:
        try:
            old_instance = LotusUser.objects.get(pk=instance.pk)
            _old_email_cache[instance.pk] = old_instance.email
        except LotusUser.DoesNotExist:
            pass


@receiver(post_save, sender=LotusUser)
def sync_django_user(sender, instance, created, **kwargs):
    """
    Sync Django User when Lotus User is created or updated.
    Creates/updates Django User to match Lotus User.
    - Admin role users get is_staff=True and is_superuser=True
    - Other users get basic Django User (created for consistency)
    """
    from django.conf import settings

    # Get old email if this was an update
    old_email = _old_email_cache.pop(instance.pk, None) if not created else None
    
    # Determine lookup email: use old email if email changed, otherwise use current email
    lookup_email = old_email if old_email and old_email != instance.email else instance.email
    
    try:
        django_user = DjangoUser.objects.get(username=lookup_email)
    except DjangoUser.DoesNotExist:
        # Create new Django User
        django_user = DjangoUser.objects.create(
            username=instance.email,
            email=instance.email,
        )

    # Update email if it changed (username stays as original email)
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
