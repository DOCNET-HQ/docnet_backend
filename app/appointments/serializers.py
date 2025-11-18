from .models import Appointment
from django.utils import timezone
from doctors.models import Doctor
from patients.models import Patient
from rest_framework import serializers
from .choices import AppointmentStatus
from patients.serializers import BasicPatientSerializer
from doctors.serializers import BasicDoctorSerializer
from meet.serializers import BasicMeetSerializer


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing appointments (minimal data)"""

    patient = BasicPatientSerializer(read_only=True)
    doctor = BasicDoctorSerializer(read_only=True)
    duration = serializers.SerializerMethodField()
    is_upcoming = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "doctor",
            "appointment_type",
            "status",
            "reason",
            "scheduled_start_time",
            "scheduled_end_time",
            "duration",
            "is_upcoming",
            "is_past",
            "timezone",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_duration(self, obj):
        if obj.duration:
            return str(obj.duration)
        return None


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed appointment view"""

    patient = BasicPatientSerializer(read_only=True)
    doctor = BasicDoctorSerializer(read_only=True)
    duration = serializers.SerializerMethodField()
    is_upcoming = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    can_cancel = serializers.SerializerMethodField()
    can_reschedule = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

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

    patient = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(), required=False, allow_null=True
    )
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(), required=False, allow_null=True
    )
    timezone = serializers.CharField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Appointment
        fields = [
            "patient",
            "doctor",
            "appointment_type",
            "scheduled_start_time",
            "scheduled_end_time",
            "timezone",
            "reason",
            "notes",
        ]

    def validate(self, data):
        """Validate appointment data"""
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError("User authentication required.")

        user = request.user
        patient = data.get("patient")
        doctor = data.get("doctor")

        # Check that at least one of doctor/patient is provided
        if not doctor and not patient:
            raise serializers.ValidationError(
                {
                    "doctor": "At least one of doctor or patient must be provided."
                }  # noqa
            )

        # Get user role
        user_role = getattr(user, "role", None)

        if user_role == "doctor":
            # Doctor must provide patient ID
            if not patient:
                raise serializers.ValidationError(
                    {
                        "patient": "Patient ID is required when a doctor is creating appointment" # noqa
                    }
                )

            data["doctor"] = user.profile

        elif user_role == "patient":
            # Patient must provide doctor ID
            if not doctor:
                raise serializers.ValidationError(
                    {
                        "doctor": "Doctor ID is required when a patient is creating appointment" # noqa
                    }  # noqa
                )

            data["patient"] = user.profile

        else:  # hospital/admin role
            if not doctor or not patient:
                raise serializers.ValidationError(
                    {
                        "doctor": "Both doctor and patient are required",
                        "patient": "Both doctor and patient are required",
                    }
                )

        # Check if end time is after start time
        if data["scheduled_end_time"] <= data["scheduled_start_time"]:
            raise serializers.ValidationError(
                {"scheduled_end_time": "End time must be after start time."}
            )

        # Check if appointment is in the past
        if data["scheduled_start_time"] < timezone.now():
            raise serializers.ValidationError(
                {
                    "scheduled_start_time": "Cannot schedule appointments in the past."  # noqa
                }
            )

        # Check for doctor availability (no overlapping appointments)
        doctor_for_availability = data.get("doctor")
        if doctor_for_availability:
            overlapping = Appointment.objects.filter(
                doctor=doctor_for_availability,
                scheduled_start_time__lt=data["scheduled_end_time"],
                scheduled_end_time__gt=data["scheduled_start_time"],
                status__in=[
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.IN_PROGRESS,
                ],
            ).exists()

            if overlapping:
                raise serializers.ValidationError(
                    {
                        "scheduled_start_time": "Doctor is not available at this time."
                    }  # noqa
                )

        return data

    def create(self, validated_data):
        # Set created_by from request user
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating appointments"""

    meet = BasicMeetSerializer(required=False, read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "appointment_type",
            "status",
            "scheduled_start_time",
            "scheduled_end_time",
            "timezone",
            "meet",
            "technical_issues_reported",
            "reason",
            "notes",
            "cancellation_reason",
            "cancelled_by",
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
                    AppointmentStatus.RESCHEDULED,
                ],
                AppointmentStatus.CONFIRMED: [
                    AppointmentStatus.IN_PROGRESS,
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.NO_SHOW,
                ],
                AppointmentStatus.IN_PROGRESS: [AppointmentStatus.COMPLETED],
            }

            if current_status in allowed_transitions:
                if value not in allowed_transitions[current_status]:
                    raise serializers.ValidationError(
                        f"Cannot change status from {current_status} to {value}"  # noqa
                    )

        return value


class AppointmentCancelSerializer(serializers.Serializer):
    """Serializer for cancelling appointments"""

    cancellation_reason = serializers.CharField(required=True)
    # cancelled_by = serializers.ChoiceField(
    #     choices=CancelledBy.choices,
    #     required=True
    # )
