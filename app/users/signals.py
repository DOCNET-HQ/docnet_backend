from django.dispatch import receiver
from django.db.models.signals import post_save
from admins.models import AdminProfile
from django.contrib.auth import get_user_model


User = get_user_model()


@receiver(post_save, sender=User)
def create_admin_profile(sender, instance, created, **kwargs):
    """
    Create a profile for admin users upon User creation.
    """

    # Ensure the profile doesn't already exist
    if (
        instance.role == 'admin' and
        not hasattr(instance, 'admin_profile')
    ):
        AdminProfile.objects.create(user=instance)
