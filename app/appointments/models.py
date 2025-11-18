import uuid
from meet.models import Meet
from django.db import models
from django.utils import timezone
from doctors.models import Doctor
from patients.models import Patient
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .choices import AppointmentType, AppointmentStatus, CancelledBy


User = get_user_model()


class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name=_("Patient"),
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name=_("Doctor"),
    )

    appointment_type = models.CharField(
        max_length=50,
        choices=AppointmentType.choices,
        default=AppointmentType.CONSULTATION,
        verbose_name=_("Appointment Type"),
    )

    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
        verbose_name=_("Status"),
        db_index=True,
    )

    scheduled_start_time = models.DateTimeField(
        verbose_name=_("Scheduled Start Time"), db_index=True
    )

    scheduled_end_time = models.DateTimeField(verbose_name=_("Scheduled End Time"))

    timezone = models.CharField(
        max_length=50,
        default="UTC",
        verbose_name=_("Timezone"),
        help_text=_("Timezone for the appointment"),
    )

    meet = models.OneToOneField(
        Meet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointment",
        verbose_name=_("Video Meeting"),
        help_text=_("Associated video meeting room"),
    )

    technical_issues_reported = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Technical Issues Reported"),
        help_text=_("Any technical issues during the appointment"),
    )

    # Administrative Fields
    reason = models.TextField(
        verbose_name=_("Reason for Visit"),
        help_text=_("Chief complaint or purpose of the appointment"),
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes/Instructions"),
        help_text=_("Special instructions for patient or provider"),
    )

    cancellation_reason = models.TextField(
        blank=True, null=True, verbose_name=_("Cancellation Reason")
    )

    cancelled_by = models.CharField(
        max_length=20,
        choices=CancelledBy.choices,
        blank=True,
        null=True,
        verbose_name=_("Cancelled By"),
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_appointments",
        verbose_name=_("Created By"),
    )

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
        ordering = ["-scheduled_start_time"]
        indexes = [
            models.Index(fields=["scheduled_start_time", "status"]),
            models.Index(fields=["patient", "scheduled_start_time"]),
            models.Index(fields=["doctor", "scheduled_start_time"]),
        ]

    def __str__(self):
        return f"{self.patient} - {self.doctor} ({self.scheduled_start_time.strftime('%Y-%m-%d %H:%M')})"  # noqa

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        super().save(*args, **kwargs)

        if is_new and self.status in [
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
        ]:
            self.create_meet_instance()

    def create_meet_instance(self):
        """Create a Meet instance and add members"""
        meet = Meet.objects.create()

        meet.members.add(self.doctor.user)
        meet.members.add(self.patient.user)

        self.meet = meet
        self.save()

    @property
    def duration(self):
        """Calculate appointment duration"""
        if self.scheduled_start_time and self.scheduled_end_time:
            return self.scheduled_end_time - self.scheduled_start_time
        return None

    @property
    def is_upcoming(self):
        """Check if appointment is upcoming"""
        return self.scheduled_start_time > timezone.now() and self.status in [
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
        ]

    @property
    def is_past(self):
        """Check if appointment is in the past"""
        return self.scheduled_end_time < timezone.now()

    def can_cancel(self):
        """Check if appointment can be cancelled"""
        return (
            self.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
            and not self.is_past
        )

    def can_reschedule(self):
        """Check if appointment can be rescheduled"""
        return (
            self.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
            and not self.is_past
        )
