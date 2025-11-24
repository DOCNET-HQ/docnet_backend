from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, filters, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Patient, PatientKYCRecord, PatientEmergencyContact
from .serializers import (
    PatientSerializer,
    PatientUpdateSerializer,
    BasicPatientSerializer,
    PatientListSerializer,
    PatientStatsSerializer,
    DoctorPatientStatsSerializer,
    HospitalPatientStatsSerializer,
    AdminPatientStatsSerializer,
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

        elif user.role == "hospital":
            # Patients that have appointments with any doctor in this hospital
            queryset = queryset.filter(
                appointments__doctor__hospital=user.profile
            ).distinct()

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


class PatientStatsViewSet(viewsets.ViewSet):
    """
    ViewSet for patient statistics
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
            return self._get_basic_stats()

    def _get_doctor_stats(self, doctor):
        """Get statistics for doctor dashboard"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_ago = now - timedelta(days=30)

        # Get patients who have appointments with this doctor
        doctor_patients = Patient.objects.filter(appointments__doctor=doctor).distinct()

        # Calculate metrics
        total_patients = doctor_patients.count()

        active_patients = doctor_patients.filter(is_active=True).count()

        pending_kyc = doctor_patients.filter(kyc_status="PENDING").count()

        verified_patients = doctor_patients.filter(kyc_status="VERIFIED").count()

        # Patients with appointments this month
        patients_this_month = (
            doctor_patients.filter(appointments__scheduled_start_time__gte=month_ago)
            .distinct()
            .count()
        )

        # New patients today (first appointment today)
        new_patients_today = (
            doctor_patients.filter(
                appointments__scheduled_start_time__date=today_start.date()
            )
            .distinct()
            .count()
        )

        # Appointment conversion rate (patients with completed appointments vs total)
        patients_with_completed_appointments = (
            doctor_patients.filter(appointments__status="completed").distinct().count()
        )

        appointment_conversion_rate = (
            (patients_with_completed_appointments / total_patients * 100)
            if total_patients > 0
            else 0
        )

        stats = {
            "total_patients": total_patients,
            "active_patients": active_patients,
            "pending_kyc": pending_kyc,
            "verified_patients": verified_patients,
            "patients_this_month": patients_this_month,
            "new_patients_today": new_patients_today,
            "appointment_conversion_rate": round(appointment_conversion_rate, 2),
        }

        serializer = DoctorPatientStatsSerializer(stats)
        return Response(serializer.data)

    def _get_hospital_stats(self, hospital):
        """Get statistics for hospital dashboard"""
        now = timezone.now()
        month_ago = now - timedelta(days=30)
        week_ago = now - timedelta(days=7)

        # Get patients who have appointments with doctors in this hospital
        hospital_patients = Patient.objects.filter(
            appointments__doctor__hospital=hospital
        ).distinct()

        # Calculate metrics
        total_patients = hospital_patients.count()

        active_patients = hospital_patients.filter(is_active=True).count()

        pending_kyc = hospital_patients.filter(kyc_status="PENDING").count()

        verified_patients = hospital_patients.filter(kyc_status="VERIFIED").count()

        # Patients with appointments this month
        patients_this_month = (
            hospital_patients.filter(appointments__scheduled_start_time__gte=month_ago)
            .distinct()
            .count()
        )

        # Patients with appointments this week
        patients_this_week = (
            hospital_patients.filter(appointments__scheduled_start_time__gte=week_ago)
            .distinct()
            .count()
        )

        # KYC completion rate
        kyc_completion_rate = (
            (verified_patients / total_patients * 100) if total_patients > 0 else 0
        )

        stats = {
            "total_patients": total_patients,
            "active_patients": active_patients,
            "pending_kyc": pending_kyc,
            "verified_patients": verified_patients,
            "patients_this_month": patients_this_month,
            "patients_this_week": patients_this_week,
            "kyc_completion_rate": round(kyc_completion_rate, 2),
        }

        serializer = HospitalPatientStatsSerializer(stats)
        return Response(serializer.data)

    def _get_admin_stats(self):
        """Get statistics for admin dashboard"""
        now = timezone.now()
        month_ago = now - timedelta(days=30)

        # Get all patients
        all_patients = Patient.objects.all()

        # Calculate metrics
        total_patients = all_patients.count()

        active_patients = all_patients.filter(is_active=True).count()

        pending_kyc = all_patients.filter(kyc_status="PENDING").count()

        verified_patients = all_patients.filter(kyc_status="VERIFIED").count()

        # Hospitals with patients
        from hospitals.models import Hospital  # Import your Hospital model

        total_hospitals_with_patients = (
            Hospital.objects.filter(doctors__appointments__patient__isnull=False)
            .distinct()
            .count()
        )

        # System-wide KYC completion rate
        system_wide_kyc_completion = (
            (verified_patients / total_patients * 100) if total_patients > 0 else 0
        )

        # Patients growth rate (this month vs last month)
        last_month_start = month_ago.replace(day=1)
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        patients_this_month = all_patients.filter(
            created_at__gte=this_month_start
        ).count()

        patients_last_month = all_patients.filter(
            created_at__gte=last_month_start, created_at__lt=this_month_start
        ).count()

        patients_growth_rate = (
            ((patients_this_month - patients_last_month) / patients_last_month * 100)
            if patients_last_month > 0
            else 0
        )

        stats = {
            "total_patients": total_patients,
            "active_patients": active_patients,
            "pending_kyc": pending_kyc,
            "verified_patients": verified_patients,
            "total_hospitals_with_patients": total_hospitals_with_patients,
            "system_wide_kyc_completion": round(system_wide_kyc_completion, 2),
            "patients_growth_rate": round(patients_growth_rate, 2),
        }

        serializer = AdminPatientStatsSerializer(stats)
        return Response(serializer.data)

    def _get_basic_stats(self):
        """Get basic statistics for other roles"""
        all_patients = Patient.objects.all()

        stats = {
            "total_patients": all_patients.count(),
            "active_patients": all_patients.filter(is_active=True).count(),
            "pending_kyc": all_patients.filter(kyc_status="PENDING").count(),
            "verified_patients": all_patients.filter(kyc_status="VERIFIED").count(),
        }

        serializer = PatientStatsSerializer(stats)
        return Response(serializer.data)
