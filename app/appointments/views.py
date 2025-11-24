from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg

from .models import Appointment
from .serializers import (
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    AppointmentCancelSerializer,
    AppointmentStatsSerializer,
    DoctorAppointmentStatsSerializer,
    HospitalAppointmentStatsSerializer,
    AdminAppointmentStatsSerializer,
)
from utils.permissions import IsDoctor
from .filters import AppointmentFilter
from .choices import AppointmentStatus
from utils.pagination import StandardResultsSetPagination


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing appointments
    """

    queryset = Appointment.objects.select_related(
        "patient", "doctor", "created_by"
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = AppointmentFilter
    search_fields = [
        "reason",
        "notes",
        "patient__name",
        "doctor__name",
    ]
    ordering_fields = ["scheduled_start_time", "created_at", "status"]
    ordering = ["-scheduled_start_time"]
    pagination_class = StandardResultsSetPagination  # Add pagination class

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return AppointmentListSerializer
        elif self.action == "create":
            return AppointmentCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return AppointmentUpdateSerializer
        elif self.action == "cancel":
            return AppointmentCancelSerializer
        return AppointmentDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        queryset = super().get_queryset()

        # If user is a doctor, show their appointments
        if hasattr(user, "doctor_profile"):
            queryset = queryset.filter(doctor=user.doctor_profile)

        # If user is a patient, show their appointments
        elif hasattr(user, "patient_profile"):
            queryset = queryset.filter(patient=user.patient_profile)

        elif hasattr(user, "hospital_profile"):
            queryset = queryset.filter(doctor__hospital=user.profile).distinct()

        elif hasattr(user, "admin_profile"):
            return queryset

        # Staff/admin can see all
        elif not user.is_staff:
            queryset = queryset.none()

        return queryset

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == "create":
            # Both doctors and patients can create appointments
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only doctors and staff can update/delete
            permission_classes = [IsAuthenticated, IsDoctor]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Set created_by when creating appointment"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="my-appointments")
    def my_appointments(self, request):
        """Get current user's appointments"""
        user = request.user

        if hasattr(user, "doctor_profile"):
            queryset = self.get_queryset().filter(doctor=user.doctor_profile)
        elif hasattr(user, "patient_profile"):
            queryset = self.get_queryset().filter(patient=user.patient_profile)
        else:
            return Response(
                {"detail": "User is neither a doctor nor a patient"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply filters
        queryset = self.filter_queryset(queryset)

        # Use pagination for this custom action
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppointmentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="upcoming")
    def upcoming_appointments(self, request):
        """Get upcoming appointments"""
        queryset = self.get_queryset().filter(
            scheduled_start_time__gt=timezone.now(),
            status__in=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED],
        )

        queryset = self.filter_queryset(queryset)

        # Use pagination for this custom action
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppointmentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="past")
    def past_appointments(self, request):
        """Get past appointments"""
        queryset = self.get_queryset().filter(scheduled_end_time__lt=timezone.now())

        queryset = self.filter_queryset(queryset)

        # Use pagination for this custom action
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppointmentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()

        if not appointment.can_cancel():
            return Response(
                {"detail": "This appointment cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Use get() method to avoid KeyError
        cancellation_reason = serializer.validated_data.get("cancellation_reason", "")

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancellation_reason = cancellation_reason
        appointment.cancelled_by = request.user.role
        appointment.save()

        return Response(
            AppointmentDetailSerializer(appointment).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        """Confirm an appointment"""
        appointment = self.get_object()

        if appointment.status != AppointmentStatus.SCHEDULED:
            return Response(
                {"detail": "Only scheduled appointments can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = AppointmentStatus.CONFIRMED
        appointment.save()

        return Response(
            AppointmentDetailSerializer(appointment).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="start")
    def start_appointment(self, request, pk=None):
        """Start an appointment (set to in-progress)"""
        appointment = self.get_object()

        # Only doctor can start appointment
        if (
            not hasattr(request.user, "doctor_profile")
            or appointment.doctor != request.user.doctor_profile
        ):  # noqa
            return Response(
                {
                    "detail": "Only the assigned doctor can start this appointment"  # noqa
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status != AppointmentStatus.CONFIRMED:
            return Response(
                {"detail": "Only confirmed appointments can be started"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = AppointmentStatus.IN_PROGRESS
        appointment.save()

        return Response(
            AppointmentDetailSerializer(appointment).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="complete")
    def complete_appointment(self, request, pk=None):
        """Complete an appointment"""
        appointment = self.get_object()

        # Only doctor can complete appointment
        if (
            not hasattr(request.user, "doctor_profile")
            or appointment.doctor != request.user.doctor_profile
        ):  # noqa
            return Response(
                {
                    "detail": "Only the assigned doctor can complete this appointment"  # noqa
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status != AppointmentStatus.IN_PROGRESS:
            return Response(
                {"detail": "Only in-progress appointments can be completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Optional: Add notes from request
        notes = request.data.get("notes", "")
        if notes:
            appointment.notes = (
                f"{appointment.notes}\n\n{notes}"
                if appointment.notes
                else notes  # noqa
            )

        appointment.status = AppointmentStatus.COMPLETED
        appointment.save()

        return Response(
            AppointmentDetailSerializer(appointment).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="report-issue")
    def report_issue(self, request, pk=None):
        """Report technical issues during appointment"""
        appointment = self.get_object()

        issue = request.data.get("issue", "")
        if not issue:
            return Response(
                {"detail": "Issue description is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if appointment.technical_issues_reported:
            appointment.technical_issues_reported = (
                f"{appointment.technical_issues_reported}\n\n{issue}"  # noqa
            )
        else:
            appointment.technical_issues_reported = issue

        appointment.save()

        return Response(
            {"detail": "Technical issue reported successfully"},
            status=status.HTTP_200_OK,
        )


class AppointmentStatsViewSet(viewsets.ViewSet):
    """
    ViewSet for appointment statistics
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="dashboard-stats")
    def dashboard_stats(self, request):
        """Get dashboard statistics based on user role"""
        user = request.user

        if hasattr(user, "doctor_profile"):
            return self._get_doctor_stats(user.doctor_profile)
        elif hasattr(user, "hospital_profile"):
            return self._get_hospital_stats(user.hospital_profile)
        elif hasattr(user, "admin_profile") or user.is_staff:
            return self._get_admin_stats()
        else:
            # For patients or other roles, return basic stats
            return self._get_basic_stats(user)

    def _get_doctor_stats(self, doctor):
        """Get statistics for doctor dashboard"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Base queryset for this doctor
        base_qs = Appointment.objects.filter(doctor=doctor)

        # Calculate metrics
        total_appointments = base_qs.count()

        today_appointments = base_qs.filter(
            scheduled_start_time__date=today_start.date(),
            status__in=["scheduled", "confirmed"],
        ).count()

        upcoming_appointments = base_qs.filter(
            scheduled_start_time__gt=now, status__in=["scheduled", "confirmed"]
        ).count()

        pending_confirmation = base_qs.filter(status="scheduled").count()

        completed_this_week = base_qs.filter(
            status="completed", scheduled_start_time__gte=week_ago
        ).count()

        # Cancellation rate (cancelled vs total in last 30 days)
        recent_appointments = base_qs.filter(scheduled_start_time__gte=month_ago)
        total_recent = recent_appointments.count()
        cancelled_recent = recent_appointments.filter(status="cancelled").count()
        cancellation_rate = (
            (cancelled_recent / total_recent * 100) if total_recent > 0 else 0
        )

        # Average daily appointments (last 30 days)
        daily_avg = (
            base_qs.filter(scheduled_start_time__gte=month_ago)
            .extra({"date": "date(scheduled_start_time)"})
            .values("date")
            .annotate(count=Count("id"))
            .aggregate(avg=Avg("count"))["avg"]
            or 0
        )

        stats = {
            "total_appointments": total_appointments,
            "today_appointments": today_appointments,
            "upcoming_appointments": upcoming_appointments,
            "pending_confirmation": pending_confirmation,
            "completed_this_week": completed_this_week,
            "cancellation_rate": round(cancellation_rate, 2),
            "average_daily_appointments": round(daily_avg, 1),
        }

        serializer = DoctorAppointmentStatsSerializer(stats)
        return Response(serializer.data)

    def _get_hospital_stats(self, hospital):
        """Get statistics for hospital dashboard"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_ago = now - timedelta(days=30)

        # Get doctors belonging to this hospital
        hospital_doctors = hospital.doctors.all()

        # Base queryset for this hospital's doctors
        base_qs = Appointment.objects.filter(doctor__in=hospital_doctors)

        # Calculate metrics
        total_appointments = base_qs.count()

        today_appointments = base_qs.filter(
            scheduled_start_time__date=today_start.date(),
            status__in=["scheduled", "confirmed"],
        ).count()

        upcoming_appointments = base_qs.filter(
            scheduled_start_time__gt=now, status__in=["scheduled", "confirmed"]
        ).count()

        pending_confirmation = base_qs.filter(status="scheduled").count()

        total_doctors_with_appointments = base_qs.values("doctor").distinct().count()

        completed_this_month = base_qs.filter(
            status="completed", scheduled_start_time__gte=month_ago
        ).count()

        stats = {
            "total_appointments": total_appointments,
            "today_appointments": today_appointments,
            "upcoming_appointments": upcoming_appointments,
            "pending_confirmation": pending_confirmation,
            "total_doctors_with_appointments": total_doctors_with_appointments,
            "completed_this_month": completed_this_month,
            # 'revenue_this_month': 0  #
        }

        serializer = HospitalAppointmentStatsSerializer(stats)
        return Response(serializer.data)

    def _get_admin_stats(self):
        """Get statistics for admin dashboard"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_ago = now - timedelta(days=30)

        # Base queryset for all appointments
        base_qs = Appointment.objects.all()

        # Calculate metrics
        total_appointments = base_qs.count()

        today_appointments = base_qs.filter(
            scheduled_start_time__date=today_start.date(),
            status__in=["scheduled", "confirmed"],
        ).count()

        upcoming_appointments = base_qs.filter(
            scheduled_start_time__gt=now, status__in=["scheduled", "confirmed"]
        ).count()

        pending_confirmation = base_qs.filter(status="scheduled").count()

        # System-wide metrics
        total_hospitals_with_appointments = (
            base_qs.filter(doctor__hospital__isnull=False)
            .values("doctor__hospital")
            .distinct()
            .count()
        )

        system_wide_completed = base_qs.filter(
            status="completed", scheduled_start_time__gte=month_ago
        ).count()

        # System-wide cancellation rate
        recent_appointments = base_qs.filter(scheduled_start_time__gte=month_ago)
        total_recent = recent_appointments.count()
        cancelled_recent = recent_appointments.filter(status="cancelled").count()
        system_wide_cancellation_rate = (
            (cancelled_recent / total_recent * 100) if total_recent > 0 else 0
        )

        stats = {
            "total_appointments": total_appointments,
            "today_appointments": today_appointments,
            "upcoming_appointments": upcoming_appointments,
            "pending_confirmation": pending_confirmation,
            "total_hospitals_with_appointments": total_hospitals_with_appointments,
            "system_wide_completed": system_wide_completed,
            "system_wide_cancellation_rate": round(system_wide_cancellation_rate, 2),
        }

        serializer = AdminAppointmentStatsSerializer(stats)
        return Response(serializer.data)

    def _get_basic_stats(self, user):
        """Get basic statistics for patients or other roles"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # For patients, show their appointments
        if hasattr(user, "patient_profile"):
            base_qs = Appointment.objects.filter(patient=user.patient_profile)
        else:
            base_qs = Appointment.objects.none()

        stats = {
            "total_appointments": base_qs.count(),
            "today_appointments": base_qs.filter(
                scheduled_start_time__date=today_start.date(),
                status__in=["scheduled", "confirmed"],
            ).count(),
            "upcoming_appointments": base_qs.filter(
                scheduled_start_time__gt=now, status__in=["scheduled", "confirmed"]
            ).count(),
            "pending_confirmation": base_qs.filter(status="scheduled").count(),
        }

        serializer = AppointmentStatsSerializer(stats)
        return Response(serializer.data)
