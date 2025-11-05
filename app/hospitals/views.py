from rest_framework import generics, status, filters, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import Hospital, HospitalKYCRecord
from .serializers import (
    HospitalSerializer,
    HospitalCreateSerializer,
    HospitalUpdateSerializer,
    BasicHospitalSerializer,
    HospitalListSerializer,
    HospitalKYCRecordSerializer,
    HospitalKYCRecordCreateSerializer,
    HospitalKYCRecordUpdateSerializer
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
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    ]
    filterset_fields = [
        'kyc_status', 'is_active', 'country', 'state', 'city'
    ]
    search_fields = [
        'name', 'registration_number', 'license_number', 'address'
    ]
    ordering_fields = [
        'name', 'created_at', 'updated_at', 'license_expiry_date'
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Additional custom filtering can be added here
        return queryset.select_related('user')


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
            raise serializers.ValidationError(
                "User already has a hospital profile."
            )
        serializer.save(user=self.request.user)


class HospitalDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single hospital by ID
    """
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return super().get_queryset().select_related('user')


class HospitalUpdateView(generics.UpdateAPIView):
    """
    Update hospital information (PUT and PATCH)
    """
    queryset = Hospital.objects.all()
    serializer_class = HospitalUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_object(self):
        # Users can only update their own hospital profile
        obj = get_object_or_404(Hospital, id=self.kwargs['id'])
        if obj.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        return obj


class HospitalDeleteView(generics.DestroyAPIView):
    """
    Delete a hospital profile
    """
    queryset = Hospital.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_object(self):
        # Users can only delete their own hospital profile
        # Admin can delete any
        obj = get_object_or_404(Hospital, id=self.kwargs['id'])
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
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
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
                status=status.HTTP_404_NOT_FOUND
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
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    ]
    filterset_fields = ['status', 'hospital__kyc_status']
    search_fields = [
        'hospital__name', 'hospital__registration_number', 'reason'
    ]
    ordering_fields = ['reviewed_at', 'status']
    ordering = ['-reviewed_at']

    def get_queryset(self):
        return super().get_queryset().select_related(
            'hospital', 'reviewed_by'
        )


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
        hospital.save(update_fields=['kyc_status'])


class HospitalKYCRecordDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single hospital KYC record
    """
    queryset = HospitalKYCRecord.objects.all()
    serializer_class = HospitalKYCRecordSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'hospital', 'reviewed_by'
        )


class HospitalKYCRecordUpdateView(generics.UpdateAPIView):
    """
    Update a hospital KYC record
    """
    queryset = HospitalKYCRecord.objects.all()
    serializer_class = HospitalKYCRecordUpdateSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def perform_update(self, serializer):
        kyc_record = serializer.save(reviewed_by=self.request.user)

        # Update the hospital's KYC status based on the record
        hospital = kyc_record.hospital
        hospital.kyc_status = kyc_record.status
        hospital.save(update_fields=['kyc_status'])


class HospitalKYCRecordDeleteView(generics.DestroyAPIView):
    """
    Delete a hospital KYC record
    """
    queryset = HospitalKYCRecord.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = 'id'


class HospitalKYCRecordsForHospitalView(generics.ListAPIView):
    """
    Get all KYC records for a specific hospital
    """
    serializer_class = HospitalKYCRecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        hospital_id = self.kwargs['hospital_id']
        hospital = get_object_or_404(Hospital, id=hospital_id)

        # Users can only view their own hospital's KYC records
        # Admins can view any
        if (
            hospital.user != self.request.user and
            not self.request.user.is_staff
        ):
            return HospitalKYCRecord.objects.none()

        return HospitalKYCRecord.objects.filter(
            hospital=hospital
        ).select_related(
            'hospital', 'reviewed_by'
        ).order_by('-reviewed_at')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hospital_stats(request):
    """
    Get statistics about hospitals
    """
    if not request.user.is_staff:
        return Response(
            {"detail": "Permission denied."},
            status=status.HTTP_403_FORBIDDEN
        )

    total_hospitals = Hospital.objects.count()
    active_hospitals = Hospital.objects.filter(is_active=True).count()
    pending_kyc = Hospital.objects.filter(kyc_status='PENDING').count()
    approved_kyc = Hospital.objects.filter(kyc_status='APPROVED').count()
    rejected_kyc = Hospital.objects.filter(kyc_status='REJECTED').count()

    stats = {
        'total_hospitals': total_hospitals,
        'active_hospitals': active_hospitals,
        'pending_kyc': pending_kyc,
        'approved_kyc': approved_kyc,
        'rejected_kyc': rejected_kyc,
        'kyc_completion_rate': round(
            (approved_kyc / total_hospitals * 100)
            if total_hospitals > 0 else 0, 2
        )
    }

    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_update_hospital_status(request):
    """
    Bulk update hospital KYC status
    """
    hospital_ids = request.data.get('hospital_ids', [])
    new_status = request.data.get('status')
    reason = request.data.get('reason', '')

    if not hospital_ids or not new_status:
        return Response(
            {"error": "hospital_ids and status are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    hospitals = Hospital.objects.filter(id__in=hospital_ids)
    updated_count = 0

    for hospital in hospitals:
        # Create KYC record
        HospitalKYCRecord.objects.create(
            hospital=hospital,
            status=new_status,
            reason=reason,
            reviewed_by=request.user
        )

        # Update hospital status
        hospital.kyc_status = new_status
        hospital.save(update_fields=['kyc_status'])
        updated_count += 1

    return Response({
        'message': f'Successfully updated {updated_count} hospitals',
        'updated_count': updated_count
    })
