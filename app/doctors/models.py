from django.db import models
from utils.choices import GENDER
from utils.file_uploads import upload_doctors_license
from hospitals.models import Hospital
from utils.validations import validate_id_file
from profiles.models import Profile, KYCRecord
from django.contrib.auth import get_user_model


User = get_user_model()


class Doctor(Profile):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="doctor_profile"
    )

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors",
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER,
        blank=True,
        null=True,
    )

    specialty = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Medical specialty of the doctor",
    )

    degree = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Highest medical degree obtained by the doctor",
    )

    years_of_experience = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Number of years the doctor has been practicing",
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
        upload_to=upload_doctors_license,
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
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"
        ordering = ["-created_at"]


class DoctorKYCRecord(KYCRecord):
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="kyc_records"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctor_kyc_reviews",
    )

    def __str__(self):
        return f"KYC Record for {self.doctor.name}"

    def save(self, *args, **kwargs):
        self.doctor.is_pending_approval = False

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Doctor KYC Record"
        verbose_name_plural = "Doctor KYC Records"
        ordering = ["-reviewed_at"]
