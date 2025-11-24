from django.db import models
from utils.validations import validate_id_file
from profiles.models import Profile, KYCRecord, Specialty
from django.contrib.auth import get_user_model
from utils.file_uploads import upload_hospitals_license
from utils.file_uploads import upload_cover_image


User = get_user_model()


class Hospital(Profile):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="hospital_profile"
    )

    specialties = models.ManyToManyField(
        Specialty,
        related_name="hospitals",
        blank=True,
    )

    cover_image = models.ImageField(upload_to=upload_cover_image, blank=True, null=True)

    registration_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Official registration number of the hospital",
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
        validators=[validate_id_file],
    )

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)

            changed = (
                old.id_document != self.id_document
                or old.license_name != self.license_name
                or old.license_issuance_authority != (self.license_issuance_authority)
                or old.license_number != self.license_number
                or old.license_issue_date != self.license_issue_date
                or old.license_expiry_date != self.license_expiry_date
                or old.license_document != self.license_document
            )

            if changed:
                self.is_pending_approval = True
                # TODO: Send email to admin to verify
                # TODO: Before they update the license details on the frontend, give them a warning saying message # noqa
                # TODO: Send email to the doctor to notify them of the change
                pass

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Hospital"
        verbose_name_plural = "Hospitals"
        ordering = ["-created_at"]


class HospitalKYCRecord(KYCRecord):
    hospital = models.ForeignKey(
        Hospital, on_delete=models.CASCADE, related_name="kyc_records"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hospital_kyc_reviews",
    )

    def __str__(self):
        return f"KYC Record for {self.hospital.name}"

    def save(self, *args, **kwargs):
        self.hospital.is_pending_approval = False

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Hospital KYC Record"
        verbose_name_plural = "Hospital KYC Records"
        ordering = ["-reviewed_at"]
