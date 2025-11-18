from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import Doctor, DoctorKYCRecord
from .serializers import (
    DoctorSerializer,
    DoctorCreateSerializer,
    DoctorUpdateSerializer,
    BasicDoctorSerializer,
    DoctorListSerializer,
    DoctorKYCRecordSerializer,
    DoctorKYCRecordCreateSerializer,
    DoctorKYCRecordUpdateSerializer,
)
from utils.permissions import IsHospital, IsPatient
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
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        kyc_record = serializer.save(reviewed_by=self.request.user)

        # Update the Doctor's KYC status based on the record
        doctor = kyc_record.doctor
        doctor.kyc_status = kyc_record.status
        doctor.save(update_fields=["kyc_status"])


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
