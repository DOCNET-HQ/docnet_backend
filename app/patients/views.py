from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import Patient, PatientKYCRecord, PatientEmergencyContact
from .serializers import (
    PatientSerializer,
    PatientUpdateSerializer,
    BasicPatientSerializer,
    PatientListSerializer,
    PatientKYCRecordSerializer,
    PatientKYCRecordCreateSerializer,
    PatientKYCRecordUpdateSerializer,
    PatientEmergencyContactSerializer,
    PatientEmergencyContactCreateSerializer,
)
from utils.pagination import StandardResultsSetPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


# Patient Views
class PatientListView(generics.ListAPIView):
    """
    List all Patients with filtering and search capabilities
    """

    queryset = Patient.objects.all()
    serializer_class = PatientListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["kyc_status", "is_active", "country", "state", "city", "gender"]
    search_fields = ["name", "phone_number", "address"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        # if is a doctor only show patients that have appointments with them
        user = self.request.user
        if user.role == "doctor":
            queryset = queryset.filter(appointments__doctor__user=user).distinct()

        return queryset.select_related("user")


# class PatientCreateView(generics.CreateAPIView):
#     """
#     Create a new Patient profile
#     """
#     queryset = Patient.objects.all()
#     serializer_class = PatientCreateSerializer
#     permission_classes = [IsAuthenticated]

#     def perform_create(self, serializer):
#         # Associate with the current user
#         serializer.save(user=self.request.user)


class PatientDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single Patient by ID
    """

    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    lookup_field = "id"

    def get_queryset(self):
        return super().get_queryset().select_related("user")


class PatientUpdateView(generics.UpdateAPIView):
    """
    Update Patient information (PUT and PATCH)
    """

    queryset = Patient.objects.all()
    serializer_class = PatientUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        # Users can only update their own Patient profile
        obj = get_object_or_404(Patient, id=self.kwargs["id"])
        if obj.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        return obj


class PatientDeleteView(generics.DestroyAPIView):
    """
    Delete a Patient profile
    """

    queryset = Patient.objects.all()
    serializer_class = PatientSerializer  # Add serializer class
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        # Users can only delete their own Patient profile
        # Admin can delete any
        obj = get_object_or_404(Patient, id=self.kwargs["id"])
        if obj.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        return obj


class MyPatientProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the current user's Patient profile
    """

    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        try:
            return Patient.objects.get(user=self.request.user)
        except Patient.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "Patient profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PatientUpdateSerializer
        return PatientSerializer


class MyBasicPatientProfileView(generics.RetrieveAPIView):
    """
    Get the current user's basic Patient profile info
    """

    serializer_class = BasicPatientSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Patient.objects.get(user=self.request.user)
        except Patient.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "Patient profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# Patient KYC Record Views
class PatientKYCRecordListView(generics.ListAPIView):
    """
    List all Patient KYC records
    """

    queryset = PatientKYCRecord.objects.all()
    serializer_class = PatientKYCRecordSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status"]
    search_fields = ["patient__name", "reason"]
    ordering_fields = ["reviewed_at", "status"]
    ordering = ["-reviewed_at"]

    def get_queryset(self):
        return super().get_queryset().select_related("patient", "reviewed_by")


class PatientKYCRecordCreateView(generics.CreateAPIView):
    """
    Create a new Patient KYC record
    """

    queryset = PatientKYCRecord.objects.all()
    serializer_class = PatientKYCRecordCreateSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        kyc_record = serializer.save(reviewed_by=self.request.user)

        # Update the Patient's KYC status based on the record
        patient = kyc_record.patient
        patient.kyc_status = kyc_record.status
        patient.save(update_fields=["kyc_status"])


class PatientKYCRecordDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single Patient KYC record
    """

    queryset = PatientKYCRecord.objects.all()
    serializer_class = PatientKYCRecordSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "id"

    def get_queryset(self):
        return super().get_queryset().select_related("patient", "reviewed_by")


class PatientKYCRecordUpdateView(generics.UpdateAPIView):
    """
    Update a Patient KYC record
    """

    queryset = PatientKYCRecord.objects.all()
    serializer_class = PatientKYCRecordUpdateSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "id"

    def perform_update(self, serializer):
        kyc_record = serializer.save(reviewed_by=self.request.user)

        # Update the Patient's KYC status based on the record
        patient = kyc_record.patient
        patient.kyc_status = kyc_record.status
        patient.save(update_fields=["kyc_status"])


class PatientKYCRecordDeleteView(generics.DestroyAPIView):
    """
    Delete a Patient KYC record
    """

    queryset = PatientKYCRecord.objects.all()
    serializer_class = PatientKYCRecordSerializer  # Add serializer class
    permission_classes = [IsAdminUser]
    lookup_field = "id"


class PatientKYCRecordsForPatientView(generics.ListAPIView):
    """
    Get all KYC records for a specific Patient
    """

    serializer_class = PatientKYCRecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        patient_id = self.kwargs["patient_id"]
        patient = get_object_or_404(Patient, id=patient_id)

        # Users can only view their own Patient's KYC records
        # Admins can view any
        if patient.user != self.request.user and not self.request.user.is_staff:
            return PatientKYCRecord.objects.none()

        return (
            PatientKYCRecord.objects.filter(patient=patient)
            .select_related("patient", "reviewed_by")
            .order_by("-reviewed_at")
        )


# Patient Emergency Contact Views
class PatientEmergencyContactListView(generics.ListAPIView):
    """
    List all emergency contacts for a patient
    """

    serializer_class = PatientEmergencyContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs["patient_id"]
        patient = get_object_or_404(Patient, id=patient_id)

        # Users can only view their own emergency contacts
        # Admins can view any
        if patient.user != self.request.user and not self.request.user.is_staff:
            return PatientEmergencyContact.objects.none()

        return PatientEmergencyContact.objects.filter(patient=patient).order_by("name")


class PatientEmergencyContactCreateView(generics.CreateAPIView):
    """
    Create a new emergency contact for a patient
    """

    serializer_class = PatientEmergencyContactCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        patient_id = self.kwargs["patient_id"]
        patient = get_object_or_404(Patient, id=patient_id)

        # Users can only create contacts for their own profile
        if patient.user != self.request.user and not self.request.user.is_staff:  # noqa
            self.permission_denied(self.request)

        serializer.save(patient=patient)


class PatientEmergencyContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an emergency contact
    """

    serializer_class = PatientEmergencyContactSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        patient_id = self.kwargs["patient_id"]
        patient = get_object_or_404(Patient, id=patient_id)

        # Users can only manage their own emergency contacts
        if patient.user != self.request.user and not self.request.user.is_staff:  # noqa
            return PatientEmergencyContact.objects.none()

        return PatientEmergencyContact.objects.filter(patient=patient)

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, id=self.kwargs["id"])
        return obj


@api_view(["GET"])
@permission_classes([IsAdminUser])
def patient_stats(request):
    """
    Get statistics about Patients
    """
    total_patients = Patient.objects.count()
    active_patients = Patient.objects.filter(is_active=True).count()
    pending_kyc = Patient.objects.filter(kyc_status="PENDING").count()
    approved_kyc = Patient.objects.filter(kyc_status="APPROVED").count()
    rejected_kyc = Patient.objects.filter(kyc_status="REJECTED").count()

    stats = {
        "total_patients": total_patients,
        "active_patients": active_patients,
        "pending_kyc": pending_kyc,
        "approved_kyc": approved_kyc,
        "rejected_kyc": rejected_kyc,
        "kyc_completion_rate": round(
            (approved_kyc / total_patients * 100) if total_patients > 0 else 0, 2
        ),
    }

    return Response(stats)
