from rest_framework import serializers
from appointments.models import Appointment


class MonthlyGrowthSerializer(serializers.Serializer):
    month = serializers.CharField()
    patients = serializers.IntegerField()
    doctors = serializers.IntegerField()
    hospitals = serializers.IntegerField()


class AppointmentTypeDistributionSerializer(serializers.Serializer):
    type = serializers.CharField()
    count = serializers.IntegerField()
    color = serializers.CharField()


class RecentAppointmentsSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(
        source="patient.name", read_only=True, required=False
    )
    doctor_name = serializers.CharField(
        source="doctor.name", read_only=True, required=False
    )
    start_time = serializers.CharField(
        source="scheduled_start_time", read_only=True, required=False
    )

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient_name",
            "doctor_name",
            "start_time",
            "status",
            "appointment_type",
        ]


class PendingApprovalsSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True, required=False)
    role = serializers.CharField(read_only=True, required=False)
    name = serializers.CharField(read_only=True, required=False)
    submitted_at = serializers.CharField(read_only=True, required=False)


class AdminDashboardSerializer(serializers.Serializer):
    total_patients = serializers.IntegerField()
    total_doctors = serializers.IntegerField()
    total_hospitals = serializers.IntegerField()

    recent_appointments = RecentAppointmentsSerializer(
        many=True, required=False, read_only=True
    )

    total_pending_approvals = serializers.IntegerField()
    pending_approvals = PendingApprovalsSerializer(
        many=True, required=False, read_only=True
    )

    # Chart data
    monthly_growth = MonthlyGrowthSerializer(many=True, required=False, read_only=True)
    appointment_distribution = AppointmentTypeDistributionSerializer(
        many=True, required=False, read_only=True
    )


class HospitalMonthlyGrowthSerializer(serializers.Serializer):
    month = serializers.CharField()
    patients = serializers.IntegerField()
    doctors = serializers.IntegerField()
    appointments = serializers.IntegerField()


class HospitalDashboardSerializer(serializers.Serializer):
    total_patients = serializers.IntegerField()
    active_doctors = serializers.IntegerField()
    total_appointments = serializers.IntegerField()

    recent_appointments = RecentAppointmentsSerializer(
        many=True, required=False, read_only=True
    )

    pending_approvals = PendingApprovalsSerializer(
        many=True, required=False, read_only=True
    )

    monthly_growth = HospitalMonthlyGrowthSerializer(
        many=True, required=False, read_only=True
    )
    appointment_distribution = AppointmentTypeDistributionSerializer(
        many=True, required=False, read_only=True
    )
