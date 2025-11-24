import calendar
from django.utils import timezone
from django.db.models import Count
from patients.models import Patient
from doctors.models import Doctor
from hospitals.models import Hospital
from datetime import datetime, timedelta
from appointments.models import Appointment
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from dashboards.serializers import (
    AdminDashboardSerializer, HospitalDashboardSerializer
)

User = get_user_model()


class AdminDashboardView(APIView):
    def get(self, request):
        # Your existing data
        total_patients = User.objects.filter(role="patient").count()
        total_doctors = User.objects.filter(role="doctor").count()
        total_hospitals = Hospital.objects.count()

        recent_appointments = Appointment.objects.all().order_by("-created_at")[:5]
        # ... your existing pending approvals logic

        # Generate monthly growth data for last 12 months
        monthly_growth_data = self.get_monthly_growth_data()

        # Generate appointment distribution data
        appointment_distribution_data = self.get_appointment_distribution_data()

        total_pending_approvals = 0
        pending_approvals_data = []

        patients_pending_approval = Patient.objects.filter(
            is_pending_approval=True
        ).order_by("-created_at")[:7]

        hospitals_pending_approval = Hospital.objects.filter(
            is_pending_approval=True
        ).order_by("-created_at")[:7]

        patient_approvals = [
            {
                "id": patient.id,
                "name": patient.name,
                "role": "patient",
                "submitted_at": patient.updated_at,
            }
            for patient in patients_pending_approval
        ]

        hospital_approvals = [
            {
                "id": hospital.id,
                "name": hospital.name,
                "role": "hospital",
                "submitted_at": hospital.updated_at,
            }
            for hospital in hospitals_pending_approval
        ]

        # Combine and get latest 7 overall
        all_pending_approvals = patient_approvals + hospital_approvals
        all_pending_approvals.sort(key=lambda x: x["submitted_at"], reverse=True)

        pending_approvals_data = all_pending_approvals[:7]

        total_pending_approvals = (
            Patient.objects.filter(is_pending_approval=True).count()
            + Hospital.objects.filter(is_pending_approval=True).count()
        )

        data = {
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "total_hospitals": total_hospitals,
            "recent_appointments": recent_appointments,
            "pending_approvals": pending_approvals_data,
            "monthly_growth": monthly_growth_data,
            "appointment_distribution": appointment_distribution_data,
            "total_pending_approvals": total_pending_approvals,
        }

        serializer = AdminDashboardSerializer(data)
        return Response(serializer.data)

    def get_monthly_growth_data(self):
        monthly_data = []
        current_date = timezone.now()

        # Generate last 12 months including current month
        for i in range(11, -1, -1):
            # Calculate start and end of each month
            target_date = current_date - timedelta(days=30 * i)
            month_start = timezone.make_aware(
                datetime(target_date.year, target_date.month, 1)
            )

            if target_date.month == 12:
                next_month = timezone.make_aware(datetime(target_date.year + 1, 1, 1))
            else:
                next_month = timezone.make_aware(
                    datetime(target_date.year, target_date.month + 1, 1)
                )

            # Get patient registrations for the month
            patients_count = User.objects.filter(
                role="patient", date_joined__gte=month_start, date_joined__lt=next_month
            ).count()

            # Get doctor registrations for the month
            doctors_count = User.objects.filter(
                role="doctor", date_joined__gte=month_start, date_joined__lt=next_month
            ).count()

            # Get hospital registrations for the month
            hospitals_count = Hospital.objects.filter(
                created_at__gte=month_start, created_at__lt=next_month
            ).count()

            monthly_data.append(
                {
                    "month": f"{calendar.month_abbr[target_date.month]} {target_date.year}", # noqa
                    "patients": patients_count,
                    "doctors": doctors_count,
                    "hospitals": hospitals_count,
                }
            )

        return monthly_data

    def get_appointment_distribution_data(self):
        # Map backend appointment types to frontend labels and colors
        type_mapping = {
            "consultation": {"label": "Consultation", "color": "#3b82f6"},
            "follow_up": {"label": "Follow-up", "color": "#10b981"},
            "general_checkup": {"label": "Checkup", "color": "#8b5cf6"},
            "urgent_care": {"label": "Emergency", "color": "#f59e0b"},
            "mental_health": {"label": "Therapy", "color": "#ef4444"},
        }

        # Get counts for each appointment type
        appointment_counts = Appointment.objects.values("appointment_type").annotate(
            count=Count("id")
        )

        distribution_data = []
        for item in appointment_counts:
            appointment_type = item["appointment_type"]
            if appointment_type in type_mapping:
                mapping = type_mapping[appointment_type]
                distribution_data.append(
                    {
                        "type": mapping["label"],
                        "count": item["count"],
                        "color": mapping["color"],
                    }
                )

        # Ensure all types are represented, even if count is 0
        for appointment_type, mapping in type_mapping.items():
            if not any(item["type"] == mapping["label"] for item in distribution_data):
                distribution_data.append(
                    {"type": mapping["label"], "count": 0, "color": mapping["color"]}
                )

        return sorted(distribution_data, key=lambda x: x["count"], reverse=True)


class HospitalDashboardView(APIView):
    def get(self, request):
        hospital = request.user.profile

        # Get all doctors belonging to this hospital
        hospital_doctors = Doctor.objects.filter(hospital=hospital)

        # Get all appointment IDs for this hospital's doctors
        hospital_appointment_ids = Appointment.objects.filter(
            doctor__in=hospital_doctors
        ).values_list("id", flat=True)

        # Patients who have appointments with this hospital's doctors
        total_patients = (
            Patient.objects.filter(
                appointments__id__in=hospital_appointment_ids
            )
            .distinct()
            .count()
        )

        # Active doctors in this hospital
        active_doctors = hospital_doctors.filter(is_active=True).count()

        # Total appointments: appointments with this hospital's doctors
        total_appointments = Appointment.objects.filter(
            doctor__in=hospital_doctors
        ).count()

        # Get recent appointments for this hospital
        recent_appointments = (
            Appointment.objects.filter(doctor__in=hospital_doctors)
            .select_related("patient", "doctor")
            .order_by("-created_at")[:5]
        )

        # Generate monthly growth data for last 12 months for this hospital
        monthly_growth_data = self.get_monthly_growth_data(hospital)

        # Generate appointment distribution data for this hospital
        appointment_distribution_data = self.get_appointment_distribution_data(hospital)

        # Get pending approvals for this hospital
        pending_approvals_data = self.get_pending_approvals_data(hospital)

        data = {
            "total_patients": total_patients,
            "active_doctors": active_doctors,
            "total_appointments": total_appointments,
            "recent_appointments": recent_appointments,
            "pending_approvals": pending_approvals_data,
            "monthly_growth": monthly_growth_data,
            "appointment_distribution": appointment_distribution_data,
        }

        serializer = HospitalDashboardSerializer(data)
        return Response(serializer.data)

    def get_monthly_growth_data(self, hospital):
        monthly_data = []
        current_date = timezone.now()

        # Get all doctors for this hospital
        hospital_doctors = Doctor.objects.filter(hospital=hospital)

        # Generate last 12 months including current month
        for i in range(11, -1, -1):
            # Calculate start and end of each month
            target_date = current_date - timedelta(days=30 * i)
            month_start = timezone.make_aware(
                datetime(target_date.year, target_date.month, 1)
            )

            if target_date.month == 12:
                next_month = timezone.make_aware(datetime(target_date.year + 1, 1, 1))
            else:
                next_month = timezone.make_aware(
                    datetime(target_date.year, target_date.month + 1, 1)
                )

            # Get appointments for this hospital in this month
            monthly_appointments = Appointment.objects.filter(
                doctor__in=hospital_doctors,
                created_at__gte=month_start,
                created_at__lt=next_month,
            )

            # Get unique patients from these appointments
            patients_count = (
                Patient.objects.filter(appointments__in=monthly_appointments)
                .distinct()
                .count()
            )

            # Get doctor registrations for the month for this hospital
            doctors_count = Doctor.objects.filter(
                hospital=hospital,
                created_at__gte=month_start,
                created_at__lt=next_month,
            ).count()

            # Get appointments count for the month
            appointments_count = monthly_appointments.count()

            monthly_data.append(
                {
                    "month": f"{calendar.month_abbr[target_date.month]} {target_date.year}", # noqa
                    "patients": patients_count,
                    "doctors": doctors_count,
                    "appointments": appointments_count,
                }
            )

        return monthly_data

    def get_appointment_distribution_data(self, hospital):
        # Map backend appointment types to frontend labels and colors
        type_mapping = {
            "consultation": {"label": "Consultation", "color": "#3b82f6"},
            "follow_up": {"label": "Follow-up", "color": "#10b981"},
            "general_checkup": {"label": "Checkup", "color": "#8b5cf6"},
            "urgent_care": {"label": "Emergency", "color": "#f59e0b"},
            "mental_health": {"label": "Therapy", "color": "#ef4444"},
        }

        # Get all doctors for this hospital
        hospital_doctors = Doctor.objects.filter(hospital=hospital)

        # Get counts for each appointment type for this hospital
        appointment_counts = (
            Appointment.objects.filter(doctor__in=hospital_doctors)
            .values("appointment_type")
            .annotate(count=Count("id"))
        )

        distribution_data = []
        for item in appointment_counts:
            appointment_type = item["appointment_type"]
            if appointment_type in type_mapping:
                mapping = type_mapping[appointment_type]
                distribution_data.append(
                    {
                        "type": mapping["label"],
                        "count": item["count"],
                        "color": mapping["color"],
                    }
                )

        # Ensure all types are represented, even if count is 0
        for appointment_type, mapping in type_mapping.items():
            if not any(item["type"] == mapping["label"] for item in distribution_data):
                distribution_data.append(
                    {"type": mapping["label"], "count": 0, "color": mapping["color"]}
                )

        return sorted(distribution_data, key=lambda x: x["count"], reverse=True)

    def get_pending_approvals_data(self, hospital):
        # Get pending doctor approvals for this hospital
        pending_doctors = Doctor.objects.filter(
            hospital=hospital, is_pending_approval=True
        ).order_by("-created_at")[:7]

        doctor_approvals = [
            {
                "id": doctor.id,
                "name": doctor.name,
                "role": "doctor",
                "submitted_at": self.format_time_ago(doctor.updated_at),
            }
            for doctor in pending_doctors
        ]

        # Combine and get latest 7 overall
        all_pending_approvals = doctor_approvals
        all_pending_approvals.sort(key=lambda x: x["submitted_at"], reverse=True)

        return all_pending_approvals[:7]

    def format_time_ago(self, updated_at):
        """Format updated_at to time ago string"""
        now = timezone.now()
        diff = now - updated_at

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds // 3600 > 0:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
