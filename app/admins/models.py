import uuid
from django.db import models
from django.contrib.auth import get_user_model
from utils.file_uploads import upload_profile_photo


User = get_user_model()


class AdminProfile(models.Model):
    # User information
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='admin_profile'
    )
    name = models.CharField(
        max_length=255,
        blank=True,
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
    )
    photo = models.ImageField(
        upload_to=upload_profile_photo,
        blank=True,
        null=True
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        help_text='Country'
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        help_text='State or Province'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text='City or Town'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name if self.name else self.user.email

    class Meta:
        verbose_name_plural = "Admin Profiles"
