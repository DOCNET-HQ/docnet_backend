from django.db import models
from utils.choices import GENDER
from profiles.models import Profile, KYCRecord
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


User = get_user_model()


class Patient(Profile):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='patient_profile'
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        ordering = ['-created_at']


class PatientKYCRecord(KYCRecord):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='kyc_records'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_kyc_reviews'
    )

    def __str__(self):
        return f"KYC Record for {self.patient.name}"

    class Meta:
        verbose_name = "Patient KYC Record"
        verbose_name_plural = "Patient KYC Records"
        ordering = ['-reviewed_at']


class PatientEmergencyContact(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='emergency_contacts'
    )
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    preferred_contact_method = models.CharField(
        max_length=10,
        choices=[
            ('phone', 'Phone'),
            ('email', 'Email'),
            ('sms', 'SMS')
        ],
        default='phone'
    )

    def __str__(self):
        return f"{self.name} ({self.relationship})"

    def clean(self):
        # Count existing contacts for this patient
        if self.patient.emergency_contacts.count() >= 2 and not self.pk:
            raise ValidationError("A patient cannot have more than 2 emergency contacts.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Patient Emergency Contact"
        verbose_name_plural = "Patient Emergency Contacts"
        ordering = ['name']
