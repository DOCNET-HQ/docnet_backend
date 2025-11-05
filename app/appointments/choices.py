from django.db import models
from django.utils.translation import gettext_lazy as _


class AppointmentType(models.TextChoices):
    CONSULTATION = 'consultation', _('Consultation')
    FOLLOW_UP = 'follow_up', _('Follow-up')
    URGENT_CARE = 'urgent_care', _('Urgent Care')
    MENTAL_HEALTH = 'mental_health', _('Mental Health Session')
    GENERAL_CHECKUP = 'general_checkup', _('General Checkup')
    SPECIALIST = 'specialist', _('Specialist Consultation')


class AppointmentStatus(models.TextChoices):
    SCHEDULED = 'scheduled', _('Scheduled')
    CONFIRMED = 'confirmed', _('Confirmed')
    IN_PROGRESS = 'in_progress', _('In Progress')
    COMPLETED = 'completed', _('Completed')
    CANCELLED = 'cancelled', _('Cancelled')
    NO_SHOW = 'no_show', _('No Show')
    RESCHEDULED = 'rescheduled', _('Rescheduled')


class CancelledBy(models.TextChoices):
    PATIENT = 'patient', _('Patient')
    DOCTOR = 'doctor', _('Doctor')
    SYSTEM = 'system', _('System')
