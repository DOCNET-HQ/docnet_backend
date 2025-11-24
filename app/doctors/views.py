from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, filters, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from .models import Doctor, DoctorKYCRecord
from .serializers import (
    DoctorSerializer,
    DoctorCreateSerializer,
    DoctorUpdateSerializer,
    BasicDoctorSerializer,
    DoctorListSerializer,
    DoctorStatsSerializer,
    HospitalDoctorStatsSerializer,
    AdminDoctorStatsSerializer,
    DoctorKYCRecordSerializer,
    DoctorKYCRecordCreateSerializer,
    DoctorKYCRecordUpdateSerializer,
)
from utils.permissions import IsHospital, IsPatient
from rest_framework.exceptions import PermissionDenied
from utils.pagination import StandardResultsSetPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


# Doctor Views
class DoctorListView(generics.ListAPIView):
    """
    List all Doctors with filtering and search capabilities
    """

    queryset = Doctor.objects.all()
    serializer_class = DoctorListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "kyc_status",
        "is_active",
        "country",
        "state",
        "city",
        "hospital__id",
    ]
    search_fields = ["name", "license_number", "address"]
    ordering_fields = ["name", "created_at", "updated_at", "license_expiry_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == "hospital":
            queryset = queryset.filter(hospital=self.request.user.hospital_profile)

        if self.request.user.role == "doctor":
            queryset = queryset.filter(
                hospital=self.request.user.doctor_profile.hospital
            ).exclude(user=self.request.user)

        # Additional custom filtering can be added here
        return queryset.select_related("user")


class MyDoctorListView(generics.ListAPIView):
    """
    List all Doctors a patient has interacted with
    """

    queryset = Doctor.objects.all()
    permission_classes = [IsAuthenticated, IsPatient]
    serializer_class = DoctorListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "kyc_status",
        "is_active",
        "country",
        "state",
        "city",
        "hospital__id",
    ]
    search_fields = ["name", "address"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()

        user = self.request.user
        patient_profile = user.patient_profile
        queryset = queryset.filter(appointments__patient=patient_profile).distinct()

        return queryset.select_related("user")


class DoctorCreateView(generics.CreateAPIView):
    """
    Create a new Doctor profile
    """

    queryset = Doctor.objects.all()
    serializer_class = DoctorCreateSerializer
    permission_classes = [IsAuthenticated, IsHospital]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        serializer.save(
            hospital=self.request.user.hospital_profile, is_active=True, is_visible=True
        )


class DoctorDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single Doctor by ID
    """

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    lookup_field = "id"

    def get_queryset(self):
        return super().get_queryset().select_related("user")


class DoctorUpdateView(generics.UpdateAPIView):
    """
    Update Doctor information (PUT and PATCH)
    """

    queryset = Doctor.objects.all()
    serializer_class = DoctorUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        # Users can only update their own Doctor profile
        obj = get_object_or_404(Doctor, id=self.kwargs["id"])
        if obj.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        return obj


class DoctorDeleteView(generics.DestroyAPIView):
    """
    Delete a Doctor profile
    """

    queryset = Doctor.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        # Users can only delete their own Doctor profile
        # Admin can delete any
        obj = get_object_or_404(Doctor, id=self.kwargs["id"])
        if obj.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        return obj


class MyDoctorProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the current user's Doctor profile
    """

    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        try:
            return Doctor.objects.get(user=self.request.user)
        except Doctor.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "Doctor profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return DoctorUpdateSerializer
        return DoctorSerializer


class MyBasicDoctorProfileView(generics.RetrieveAPIView):
    """
    Get the current user's basic Doctor profile info
    """

    serializer_class = BasicDoctorSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Doctor.objects.get(user=self.request.user)
        except Doctor.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "Doctor profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# Doctor KYC Record Views
class DoctorKYCRecordListView(generics.ListAPIView):
    """
    List all Doctor KYC records
    """

    queryset = DoctorKYCRecord.objects.all()
    serializer_class = DoctorKYCRecordSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status"]
    search_fields = ["doctor__name", "doctor__registration_number", "reason"]
    ordering_fields = ["reviewed_at", "status"]
    ordering = ["-reviewed_at"]

    def get_queryset(self):
        return super().get_queryset().select_related("doctor", "reviewed_by")


class DoctorKYCRecordCreateView(generics.CreateAPIView):
    """
    Create a new Doctor KYC record
    """

    queryset = DoctorKYCRecord.objects.all()
    serializer_class = DoctorKYCRecordCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        doctor = serializer.validated_data.get("doctor")

        if user.role == "admin" or doctor.hospital.user == user:
            kyc_record = serializer.save(reviewed_by=self.request.user)

            # Update the Doctor's KYC status based on the record
            doctor = kyc_record.doctor
            doctor.kyc_status = kyc_record.status
            doctor.save(update_fields=["kyc_status"])

        else:
            raise PermissionDenied(
                "You do not have permission to access this resource."
            )


class DoctorKYCRecordDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single Doctor KYC record
    """

    queryset = DoctorKYCRecord.objects.all()
    serializer_class = DoctorKYCRecordSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "id"

    def get_queryset(self):
        return super().get_queryset().select_related("Doctor", "reviewed_by")


class DoctorKYCRecordUpdateView(generics.UpdateAPIView):
    """
    Update a Doctor KYC record
    """

    queryset = DoctorKYCRecord.objects.all()
    serializer_class = DoctorKYCRecordUpdateSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "id"

    def perform_update(self, serializer):
        kyc_record = serializer.save(reviewed_by=self.request.user)

        # Update the Doctor's KYC status based on the record
        doctor = kyc_record.doctor
        doctor.kyc_status = kyc_record.status
        doctor.save(update_fields=["kyc_status"])


class DoctorKYCRecordDeleteView(generics.DestroyAPIView):
    """
    Delete a Doctor KYC record
    """

    queryset = DoctorKYCRecord.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = "id"


class DoctorKYCRecordsForDoctorView(generics.ListAPIView):
    """
    Get all KYC records for a specific Doctor
    """

    serializer_class = DoctorKYCRecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        doctor_id = self.kwargs["doctor_id"]
        doctor = get_object_or_404(Doctor, id=doctor_id)

        # Users can only view their own Doctor's KYC records
        # Admins can view any
        if doctor.user != self.request.user and not self.request.user.is_staff:
            return DoctorKYCRecord.objects.none()

        return (
            DoctorKYCRecord.objects.filter(doctor=doctor)
            .select_related("doctor", "reviewed_by")
            .order_by("-reviewed_at")
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def Doctor_stats(request):
    """
    Get statistics about Doctors
    """
    if not request.user.is_staff:
        return Response(
            {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
        )

    total_doctors = Doctor.objects.count()
    active_doctors = Doctor.objects.filter(is_active=True).count()
    pending_kyc = Doctor.objects.filter(kyc_status="PENDING").count()
    approved_kyc = Doctor.objects.filter(kyc_status="APPROVED").count()
    rejected_kyc = Doctor.objects.filter(kyc_status="REJECTED").count()

    stats = {
        "total_doctors": total_doctors,
        "active_doctors": active_doctors,
        "pending_kyc": pending_kyc,
        "approved_kyc": approved_kyc,
        "rejected_kyc": rejected_kyc,
        "kyc_completion_rate": round(
            (approved_kyc / total_doctors * 100) if total_doctors > 0 else 0, 2
        ),
    }

    return Response(stats)


class DoctorStatsViewSet(viewsets.ViewSet):
    """
    ViewSet for doctor statistics
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="dashboard-stats")
    def dashboard_stats(self, request):
        """Get dashboard statistics based on user role"""
        user = request.user

        if hasattr(user, "hospital_profile"):
            return self._get_hospital_stats(user.hospital_profile)
        elif hasattr(user, "admin_profile") or user.is_staff:
            return self._get_admin_stats()
        else:
            # For doctors or other roles, return basic stats
            return self._get_basic_stats()

    def _get_hospital_stats(self, hospital):
        """Get statistics for hospital dashboard"""
        now = timezone.now()
        month_ago = now - timedelta(days=30)

        # Get doctors belonging to this hospital
        hospital_doctors = hospital.doctors.all()

        # Calculate metrics
        total_doctors = hospital_doctors.count()

        active_doctors = hospital_doctors.filter(is_active=True).count()

        verified_doctors = hospital_doctors.filter(kyc_status="VERIFIED").count()

        pending_kyc = hospital_doctors.filter(kyc_status="PENDING").count()

        # Doctors joined this month
        doctors_this_month = hospital_doctors.filter(created_at__gte=month_ago).count()

        avg_patients_data = hospital_doctors.annotate(
            patient_count=Count("appointments__patient", distinct=True)
        ).aggregate(avg=Avg("patient_count"))
        average_patients_per_doctor = avg_patients_data["avg"] or 0

        # Top specialties
        top_specialties = (
            hospital_doctors.values("specialty")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        stats = {
            "total_doctors": total_doctors,
            "active_doctors": active_doctors,
            "verified_doctors": verified_doctors,
            "pending_kyc": pending_kyc,
            "doctors_this_month": doctors_this_month,
            "average_patients_per_doctor": round(average_patients_per_doctor, 1),
            "top_specialties": list(top_specialties),
        }

        serializer = HospitalDoctorStatsSerializer(stats)
        return Response(serializer.data)

    def _get_admin_stats(self):
        """Get statistics for admin dashboard"""
        now = timezone.now()
        month_ago = now - timedelta(days=30)

        # Get all doctors
        all_doctors = Doctor.objects.all()

        # Calculate metrics
        total_doctors = all_doctors.count()

        active_doctors = all_doctors.filter(is_active=True).count()

        verified_doctors = all_doctors.filter(kyc_status="VERIFIED").count()

        pending_kyc = all_doctors.filter(kyc_status="PENDING").count()

        # Hospitals with doctors
        from hospitals.models import Hospital

        total_hospitals_with_doctors = (
            Hospital.objects.filter(doctors__isnull=False).distinct().count()
        )

        # System-wide KYC completion rate
        system_wide_kyc_completion = (
            (verified_doctors / total_doctors * 100) if total_doctors > 0 else 0
        )

        # Doctors growth rate (this month vs last month)
        last_month_start = month_ago.replace(day=1)
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        doctors_this_month = all_doctors.filter(
            created_at__gte=this_month_start
        ).count()

        doctors_last_month = all_doctors.filter(
            created_at__gte=last_month_start, created_at__lt=this_month_start
        ).count()

        doctors_growth_rate = (
            ((doctors_this_month - doctors_last_month) / doctors_last_month * 100)
            if doctors_last_month > 0
            else 0
        )

        # Specialties distribution
        specialties_distribution = (
            all_doctors.values("specialty")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )

        stats = {
            "total_doctors": total_doctors,
            "active_doctors": active_doctors,
            "verified_doctors": verified_doctors,
            "pending_kyc": pending_kyc,
            "total_hospitals_with_doctors": total_hospitals_with_doctors,
            "system_wide_kyc_completion": round(system_wide_kyc_completion, 2),
            "doctors_growth_rate": round(doctors_growth_rate, 2),
            "specialties_distribution": list(specialties_distribution),
        }

        serializer = AdminDoctorStatsSerializer(stats)
        return Response(serializer.data)

    def _get_basic_stats(self):
        """Get basic statistics for other roles"""
        all_doctors = Doctor.objects.all()

        stats = {
            "total_doctors": all_doctors.count(),
            "active_doctors": all_doctors.filter(is_active=True).count(),
            "verified_doctors": all_doctors.filter(kyc_status="VERIFIED").count(),
            "pending_kyc": all_doctors.filter(kyc_status="PENDING").count(),
        }

        serializer = DoctorStatsSerializer(stats)
        return Response(serializer.data)
