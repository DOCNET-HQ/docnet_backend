from django.db import models
from utils.file_uploads import (
    upload_hospitals_license
)
from utils.validations import validate_id_file
from profiles.models import Profile, KYCRecord
from django.contrib.auth import get_user_model


User = get_user_model()


class Hospital(Profile):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='hospital_profile'
    )

    registration_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Official registration number of the hospital'
    )

    # License information
    license_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    license_issuance_authority = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    license_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )
    license_issue_date = models.DateField(null=True, blank=True)
    license_expiry_date = models.DateField(null=True, blank=True)
    license_document = models.FileField(
        upload_to=upload_hospitals_license,
        blank=True,
        null=True,
        validators=[validate_id_file]
    )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            original = Hospital.objects.get(pk=self.pk)
            if (
                original.license_number != self.license_number or
                original.license_expiry_date != self.license_expiry_date or
                original.license_document != self.license_document
            ):
                # TODO: Send email to admin to verify
                # TODO: Before they update the license details on the frontend, give them a warning saying message # noqa
                # TODO: Send email to the hospital to notify them of the change
                pass

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Hospital'
        verbose_name_plural = 'Hospitals'
        ordering = ['-created_at']


class HospitalKYCRecord(KYCRecord):
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name='kyc_records'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hospital_kyc_reviews'
    )

    def __str__(self):
        return f"KYC Record for {self.hospital.name}"

    class Meta:
        verbose_name = "Hospital KYC Record"
        verbose_name_plural = "Hospital KYC Records"
        ordering = ['-reviewed_at']
