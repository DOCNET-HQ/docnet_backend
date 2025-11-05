from .models import Appointment
from django.utils import timezone
from rest_framework import serializers
from .choices import AppointmentStatus, CancelledBy


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing appointments (minimal data)"""

    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    is_upcoming = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'appointment_type', 'status', 'scheduled_start_time',
            'scheduled_end_time', 'duration', 'is_upcoming', 'is_past',
            'timezone', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_patient_name(self, obj):
        return f"{obj.patient.user.first_name} {obj.patient.user.last_name}"

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.first_name} {obj.doctor.user.last_name}"

    def get_duration(self, obj):
        if obj.duration:
            return str(obj.duration)
        return None


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed appointment view"""

    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    is_upcoming = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    can_cancel = serializers.SerializerMethodField()
    can_reschedule = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_patient_name(self, obj):
        return f"{obj.patient.user.first_name} {obj.patient.user.last_name}"

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.first_name} {obj.doctor.user.last_name}"

    def get_duration(self, obj):
        if obj.duration:
            return str(obj.duration)
        return None

    def get_can_cancel(self, obj):
        return obj.can_cancel()

    def get_can_reschedule(self, obj):
        return obj.can_reschedule()


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating appointments"""

    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'appointment_type', 'scheduled_start_time',
            'scheduled_end_time', 'timezone', 'reason', 'notes'
        ]

    def validate(self, data):
        """Validate appointment data"""

        # Check if end time is after start time
        if data['scheduled_end_time'] <= data['scheduled_start_time']:
            raise serializers.ValidationError({
                'scheduled_end_time': 'End time must be after start time.'
            })

        # Check if appointment is in the past
        if data['scheduled_start_time'] < timezone.now():
            raise serializers.ValidationError({
                'scheduled_start_time': 'Cannot schedule appointments in the past.' # noqa
            })

        # Check for doctor availability (no overlapping appointments)
        doctor = data['doctor']
        overlapping = Appointment.objects.filter(
            doctor=doctor,
            scheduled_start_time__lt=data['scheduled_end_time'],
            scheduled_end_time__gt=data['scheduled_start_time'],
            status__in=[
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.IN_PROGRESS
            ]
        ).exists()

        if overlapping:
            raise serializers.ValidationError({
                'scheduled_start_time': 'Doctor is not available at this time.'
            })

        return data

    def create(self, validated_data):
        # Set created_by from request user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating appointments"""

    class Meta:
        model = Appointment
        fields = [
            'appointment_type', 'status', 'scheduled_start_time',
            'scheduled_end_time', 'timezone', 'meeting_link',
            'technical_issues_reported', 'reason', 'notes',
            'cancellation_reason', 'cancelled_by'
        ]

    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance:
            current_status = self.instance.status

            # Define allowed transitions
            allowed_transitions = {
                AppointmentStatus.SCHEDULED: [
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.RESCHEDULED
                ],
                AppointmentStatus.CONFIRMED: [
                    AppointmentStatus.IN_PROGRESS,
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.NO_SHOW
                ],
                AppointmentStatus.IN_PROGRESS: [
                    AppointmentStatus.COMPLETED
                ],
            }

            if current_status in allowed_transitions:
                if value not in allowed_transitions[current_status]:
                    raise serializers.ValidationError(
                        f"Cannot change status from {current_status} to {value}" # noqa
                    )

        return value


class AppointmentCancelSerializer(serializers.Serializer):
    """Serializer for cancelling appointments"""

    cancellation_reason = serializers.CharField(required=True)
    cancelled_by = serializers.ChoiceField(
        choices=CancelledBy.choices,
        required=True
    )
