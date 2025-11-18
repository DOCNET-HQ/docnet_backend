from .models import Appointment
from django.utils import timezone
from django_filters.rest_framework import (
    FilterSet,
    DateTimeFilter,
    CharFilter,
    ChoiceFilter,
)
from .choices import AppointmentStatus, AppointmentType


class AppointmentFilter(FilterSet):
    """Custom filter for appointments"""

    start_date = DateTimeFilter(field_name="scheduled_start_time", lookup_expr="gte")
    end_date = DateTimeFilter(field_name="scheduled_start_time", lookup_expr="lte")
    status = ChoiceFilter(choices=AppointmentStatus.choices)
    appointment_type = ChoiceFilter(choices=AppointmentType.choices)
    doctor_id = CharFilter(field_name="doctor__id")
    patient_id = CharFilter(field_name="patient__id")
    is_upcoming = CharFilter(method="filter_upcoming")
    is_past = CharFilter(method="filter_past")

    class Meta:
        model = Appointment
        fields = [
            "status",
            "appointment_type",
            "doctor_id",
            "patient_id",
            "start_date",
            "end_date",
        ]

    def filter_upcoming(self, queryset, name, value):
        if value.lower() in ["true", "1"]:
            return queryset.filter(
                scheduled_start_time__gt=timezone.now(),
                status__in=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED],
            )
        return queryset

    def filter_past(self, queryset, name, value):
        if value.lower() in ["true", "1"]:
            return queryset.filter(scheduled_end_time__lt=timezone.now())
        return queryset
