from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets
from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Hospital, HospitalKYCRecord
from rest_framework import generics, status, filters, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .filters import HospitalFilter, HospitalKYCRecordFilter
from .serializers import (
    HospitalSerializer,
    HospitalDetailSerializer,
    HospitalCreateSerializer,
    HospitalUpdateSerializer,
    BasicHospitalSerializer,
    HospitalListSerializer,
    HospitalStatsSerializer,
    AdminHospitalStatsSerializer,
    BasicHospitalStatsSerializer,
    HospitalKYCRecordSerializer,
    HospitalKYCRecordCreateSerializer,
    HospitalKYCRecordUpdateSerializer,
)
from utils.pagination import StandardResultsSetPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


# Hospital Views
class HospitalListView(generics.ListAPIView):
    """
    List all hospitals with filtering and search capabilities
    """

    queryset = Hospital.objects.all()
    serializer_class = HospitalListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = HospitalFilter
    search_fields = ["name", "registration_number", "license_number", "address"]
    ordering_fields = ["name", "created_at", "updated_at", "license_expiry_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Additional custom filtering can be added here
        return queryset.select_related("user")


class HospitalCreateView(generics.CreateAPIView):
    """
    Create a new hospital profile
    """

    queryset = Hospital.objects.all()
    serializer_class = HospitalCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Check if user already has a hospital profile
        if Hospital.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError("User already has a hospital profile.")
        serializer.save(user=self.request.user)


class HospitalDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single hospital by ID
    """

    queryset = Hospital.objects.all()
    serializer_class = HospitalDetailSerializer
    lookup_field = "id"

    def get_queryset(self):
        return super().get_queryset().select_related("user")


class HospitalUpdateView(generics.UpdateAPIView):
    """
    Update hospital information (PUT and PATCH)
    """

    queryset = Hospital.objects.all()
    serializer_class = HospitalUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        # Users can only update their own hospital profile
        obj = get_object_or_404(Hospital, id=self.kwargs["id"])
        if obj.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        return obj


class HospitalDeleteView(generics.DestroyAPIView):
    """
    Delete a hospital profile
    """

    queryset = Hospital.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        # Users can only delete their own hospital profile
        # Admin can delete any
        obj = get_object_or_404(Hospital, id=self.kwargs["id"])
        if obj.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        return obj


class MyHospitalProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the current user's hospital profile
    """

    serializer_class = HospitalSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        try:
            return Hospital.objects.get(user=self.request.user)
        except Hospital.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "Hospital profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return HospitalUpdateSerializer
        return HospitalSerializer


class MyBasicHospitalProfileView(generics.RetrieveAPIView):
    """
    Get the current user's basic hospital profile info
    """

    serializer_class = BasicHospitalSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Hospital.objects.get(user=self.request.user)
        except Hospital.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "Hospital profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# Hospital KYC Record Views
class HospitalKYCRecordListView(generics.ListAPIView):
    """
    List all hospital KYC records
    """

    queryset = HospitalKYCRecord.objects.all()
    serializer_class = HospitalKYCRecordSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = HospitalKYCRecordFilter
    search_fields = ["hospital__name", "hospital__registration_number", "reason"]
    ordering_fields = ["reviewed_at", "status"]
    ordering = ["-reviewed_at"]

    def get_queryset(self):
        return super().get_queryset().select_related("hospital", "reviewed_by")


class HospitalKYCRecordCreateView(generics.CreateAPIView):
    """
    Create a new hospital KYC record
    """

    queryset = HospitalKYCRecord.objects.all()
    serializer_class = HospitalKYCRecordCreateSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        kyc_record = serializer.save(reviewed_by=self.request.user)

        # Update the hospital's KYC status based on the record
        hospital = kyc_record.hospital
        hospital.kyc_status = kyc_record.status
        hospital.save(update_fields=["kyc_status"])


class HospitalKYCRecordDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single hospital KYC record
    """

    queryset = HospitalKYCRecord.objects.all()
    serializer_class = HospitalKYCRecordSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "id"

    def get_queryset(self):
        return super().get_queryset().select_related("hospital", "reviewed_by")


class HospitalKYCRecordUpdateView(generics.UpdateAPIView):
    """
    Update a hospital KYC record
    """

    queryset = HospitalKYCRecord.objects.all()
    serializer_class = HospitalKYCRecordUpdateSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "id"

    def perform_update(self, serializer):
        kyc_record = serializer.save(reviewed_by=self.request.user)

        # Update the hospital's KYC status based on the record
        hospital = kyc_record.hospital
        hospital.kyc_status = kyc_record.status
        hospital.save(update_fields=["kyc_status"])


class HospitalKYCRecordDeleteView(generics.DestroyAPIView):
    """
    Delete a hospital KYC record
    """

    queryset = HospitalKYCRecord.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = "id"


class HospitalKYCRecordsForHospitalView(generics.ListAPIView):
    """
    Get all KYC records for a specific hospital
    """

    serializer_class = HospitalKYCRecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        hospital_id = self.kwargs["hospital_id"]
        hospital = get_object_or_404(Hospital, id=hospital_id)

        # Users can only view their own hospital's KYC records
        # Admins can view any
        if hospital.user != self.request.user and not self.request.user.is_staff:
            return HospitalKYCRecord.objects.none()

        return (
            HospitalKYCRecord.objects.filter(hospital=hospital)
            .select_related("hospital", "reviewed_by")
            .order_by("-reviewed_at")
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def bulk_update_hospital_status(request):
    """
    Bulk update hospital KYC status
    """
    hospital_ids = request.data.get("hospital_ids", [])
    new_status = request.data.get("status")
    reason = request.data.get("reason", "")

    if not hospital_ids or not new_status:
        return Response(
            {"error": "hospital_ids and status are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    hospitals = Hospital.objects.filter(id__in=hospital_ids)
    updated_count = 0

    for hospital in hospitals:
        # Create KYC record
        HospitalKYCRecord.objects.create(
            hospital=hospital,
            status=new_status,
            reason=reason,
            reviewed_by=request.user,
        )

        # Update hospital status
        hospital.kyc_status = new_status
        hospital.save(update_fields=["kyc_status"])
        updated_count += 1

    return Response(
        {
            "message": f"Successfully updated {updated_count} hospitals",
            "updated_count": updated_count,
        }
    )


class HospitalStatsViewSet(viewsets.ViewSet):
    """
    ViewSet for hospital statistics
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="dashboard-stats")
    def dashboard_stats(self, request):
        """Get dashboard statistics based on user role"""
        user = request.user

        if hasattr(user, "hospital_profile"):
            return self._get_hospital_admin_stats(user.hospital_profile)
        elif hasattr(user, "admin_profile") or user.is_staff:
            return self._get_admin_stats()
        else:
            # For doctors or other roles, return basic stats
            return self._get_basic_stats()

    def _get_hospital_admin_stats(self, hospital):
        """Get statistics for hospital admin dashboard"""
        now = timezone.now()
        month_ago = now - timedelta(days=30)

        # Get this hospital's data
        hospital_obj = Hospital.objects.get(id=hospital.id)

        # Calculate metrics
        total_doctors = hospital_obj.doctors.count()

        active_doctors = hospital_obj.doctors.filter(is_active=True).count()

        # Hospital rating
        hospital_rating = (
            hospital_obj.rating.average if hasattr(hospital_obj, "rating") else 0
        )

        # Total reviews
        total_reviews = (
            hospital_obj.rating.total_reviews if hasattr(hospital_obj, "rating") else 0
        )

        # New doctors this month
        doctors_this_month = hospital_obj.doctors.filter(
            created_at__gte=month_ago
        ).count()

        # Appointment statistics (assuming you have an appointments model)
        from appointments.models import Appointment

        appointments_this_month = Appointment.objects.filter(
            doctor__in=hospital_obj.doctors.all(), created_at__gte=month_ago
        ).count()

        # Top performing specialties
        top_specialties = (
            hospital_obj.doctors.values("specialty")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        stats = {
            "total_doctors": total_doctors,
            "active_doctors": active_doctors,
            "hospital_rating": round(hospital_rating, 1),
            "total_reviews": total_reviews,
            "doctors_this_month": doctors_this_month,
            "appointments_this_month": appointments_this_month,
            "top_specialties": list(top_specialties),
        }

        serializer = HospitalStatsSerializer(stats)
        return Response(serializer.data)

    def _get_admin_stats(self):
        """Get statistics for admin dashboard"""
        now = timezone.now()
        month_ago = now - timedelta(days=30)

        # Get all hospitals
        all_hospitals = Hospital.objects.all()

        # Calculate metrics
        total_hospitals = all_hospitals.count()

        verified_hospitals = all_hospitals.filter(kyc_status="VERIFIED").count()

        active_hospitals = all_hospitals.filter(is_active=True).count()

        pending_kyc = all_hospitals.filter(kyc_status="PENDING").count()

        # Hospitals with doctors
        total_hospitals_with_doctors = (
            all_hospitals.filter(doctors__isnull=False).distinct().count()
        )

        # Cities covered
        total_cities = all_hospitals.values("city").distinct().count()

        # System-wide KYC completion rate
        system_wide_kyc_completion = (
            (verified_hospitals / total_hospitals * 100) if total_hospitals > 0 else 0
        )

        # Hospitals growth rate (this month vs last month)
        last_month_start = month_ago.replace(day=1)
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        hospitals_this_month = all_hospitals.filter(
            created_at__gte=this_month_start
        ).count()

        hospitals_last_month = all_hospitals.filter(
            created_at__gte=last_month_start, created_at__lt=this_month_start
        ).count()

        hospitals_growth_rate = (
            ((hospitals_this_month - hospitals_last_month) / hospitals_last_month * 100)
            if hospitals_last_month > 0
            else 0
        )

        # Total specialties across all hospitals
        from doctors.models import Doctor

        total_specialties = Doctor.objects.values("specialty").distinct().count()

        # Top cities by hospital count
        top_cities = (
            all_hospitals.values("city", "state")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        stats = {
            "total_hospitals": total_hospitals,
            "verified_hospitals": verified_hospitals,
            "active_hospitals": active_hospitals,
            "pending_kyc": pending_kyc,
            "total_hospitals_with_doctors": total_hospitals_with_doctors,
            "total_cities": total_cities,
            "system_wide_kyc_completion": round(system_wide_kyc_completion, 2),
            "hospitals_growth_rate": round(hospitals_growth_rate, 2),
            "total_specialties": total_specialties,
            "top_cities": list(top_cities),
        }

        serializer = AdminHospitalStatsSerializer(stats)
        return Response(serializer.data)

    def _get_basic_stats(self):
        """Get basic statistics for other roles"""
        all_hospitals = Hospital.objects.all()

        stats = {
            "total_hospitals": all_hospitals.count(),
            "verified_hospitals": all_hospitals.filter(kyc_status="VERIFIED").count(),
            "active_hospitals": all_hospitals.filter(is_active=True).count(),
            "pending_kyc": all_hospitals.filter(kyc_status="PENDING").count(),
        }

        serializer = BasicHospitalStatsSerializer(stats)
        return Response(serializer.data)
