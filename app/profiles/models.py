import uuid
from django.db import models
from .choices import KYC_STATUS
from django.contrib.auth import get_user_model
from utils.validations import validate_id_file
from utils.file_uploads import (
    upload_id_documents,
    upload_profile_photo,
    upload_specialty_img,
)


User = get_user_model()


class Profile(models.Model):
    # User information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        blank=True,
    )
    dob = models.DateField(blank=True, null=True, help_text="Date of Birth")
    phone_number = models.CharField(
        max_length=15,
        blank=True,
    )
    website = models.URLField(blank=True, null=True)

    bio = models.TextField(blank=True, null=True)

    photo = models.ImageField(upload_to=upload_profile_photo, blank=True, null=True)

    # Address information
    address = models.CharField(
        max_length=255,
        blank=True,
    )
    country = models.CharField(max_length=100, blank=True, help_text="Country")
    state = models.CharField(max_length=100, blank=True, help_text="State or Province")
    city = models.CharField(max_length=100, blank=True, help_text="City or Town")
    postal_code = models.CharField(max_length=20, blank=True)

    # KYC Information
    id_document = models.FileField(
        upload_to=upload_id_documents,
        null=True,
        blank=True,
        validators=[validate_id_file],
    )

    kyc_status = models.CharField(
        max_length=10,
        choices=KYC_STATUS,
        default="PENDING",
        help_text="KYC status of the user",
    )

    is_active = models.BooleanField(default=True)
    is_visible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class KYCRecord(models.Model):
    status = models.CharField(max_length=20, choices=KYC_STATUS, default="PENDING")
    reason = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to=upload_specialty_img,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Specialty"
        verbose_name_plural = "Specialties"
        ordering = ["name"]
