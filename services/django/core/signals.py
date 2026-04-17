"""
Signals to sync Django Users with Lotus Users.
Keeps Django auth.User in sync with core.User for admin access.
"""

from django.contrib.auth.models import User as DjangoUser
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver

from .auth_utils import desired_django_access_flags
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
    old_email = _old_email_cache.pop(instance.pk, None) if not created else None

    # Look up the existing Django User by its prior email so we can carry the row
    # through an email change; the username stays pinned to the original address.
    lookup_email = old_email if old_email and old_email != instance.email else instance.email

    try:
        django_user = DjangoUser.objects.get(username=lookup_email)
    except DjangoUser.DoesNotExist:
        django_user = DjangoUser.objects.create(
            username=instance.email,
            email=instance.email,
        )

    if django_user.email != instance.email:
        django_user.email = instance.email
        django_user.save()

    is_staff, is_superuser = desired_django_access_flags(
        django_user=django_user,
        lotus_user=instance,
    )
    django_user.is_staff = is_staff
    django_user.is_superuser = is_superuser
    django_user.save()


@receiver(m2m_changed, sender=DjangoUser.groups.through)
def sync_django_user_group_access(sender, instance, action, **kwargs):
    """Keep Django staff access aligned when admin-allowed groups change."""
    if action not in {"post_add", "post_remove", "post_clear"}:
        return

    lotus_user = LotusUser.objects.filter(email=instance.email).first()
    if not lotus_user:
        return

    is_staff, is_superuser = desired_django_access_flags(
        django_user=instance,
        lotus_user=lotus_user,
    )
    if instance.is_staff == is_staff and instance.is_superuser == is_superuser:
        return

    instance.is_staff = is_staff
    instance.is_superuser = is_superuser
    instance.save(update_fields=["is_staff", "is_superuser"])


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
