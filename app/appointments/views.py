from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Appointment
from .serializers import (
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    AppointmentCancelSerializer,
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
        "patient__user__first_name",
        "patient__user__last_name",
        "doctor__user__first_name",
        "doctor__user__last_name",
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
            status__in=[
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED
            ],
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
        queryset = self.get_queryset().filter(
            scheduled_end_time__lt=timezone.now()
        )

        queryset = self.filter_queryset(queryset)

        # Use pagination for this custom action
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppointmentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)

    # The rest of your methods remain the same...
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()

        if not appointment.can_cancel():
            return Response(
                {"detail": "This appointment cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AppointmentCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancellation_reason = serializer.validated_data[
            "cancellation_reason"
        ]
        appointment.cancelled_by = serializer.validated_data["cancelled_by"]
        appointment.save()

        return Response(
            AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_200_OK
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
            AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_200_OK
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
                    "detail": "Only the assigned doctor can start this appointment" # noqa
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
            AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_200_OK
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
                f"{appointment.notes}\n\n{notes}" if appointment.notes else notes # noqa
            )

        appointment.status = AppointmentStatus.COMPLETED
        appointment.save()

        return Response(
            AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_200_OK
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
