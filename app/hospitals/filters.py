import django_filters
from django.db.models import Q
from .models import Hospital, HospitalKYCRecord


class HospitalFilter(django_filters.FilterSet):
    """
    Advanced filtering for Hospital model
    """
    name = django_filters.CharFilter(lookup_expr='icontains')
    registration_number = django_filters.CharFilter(lookup_expr='icontains')
    license_number = django_filters.CharFilter(lookup_expr='icontains')
    phone_number = django_filters.CharFilter(lookup_expr='icontains')

    # Location filters
    country = django_filters.CharFilter(lookup_expr='iexact')
    state = django_filters.CharFilter(lookup_expr='icontains')
    city = django_filters.CharFilter(lookup_expr='icontains')

    # Date filters
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    license_expires_after = django_filters.DateFilter(field_name='license_expiry_date', lookup_expr='gte')
    license_expires_before = django_filters.DateFilter(field_name='license_expiry_date', lookup_expr='lte')

    # Status filters
    kyc_status = django_filters.ChoiceFilter(choices=[
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REQUIRES_UPDATE', 'Requires Update'),
    ])
    is_active = django_filters.BooleanFilter()

    # License authority filter
    license_authority = django_filters.CharFilter(
        field_name='license_issuance_authority',
        lookup_expr='icontains'
    )

    # Search across multiple fields
    search = django_filters.CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        """
        Search across multiple fields
        """
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(registration_number__icontains=value) |
                Q(license_number__icontains=value) |
                Q(address__icontains=value) |
                Q(city__icontains=value) |
                Q(state__icontains=value) |
                Q(phone_number__icontains=value)
            )
        return queryset

    class Meta:
        model = Hospital
        fields = {
            'name': ['exact', 'icontains'],
            'kyc_status': ['exact'],
            'is_active': ['exact'],
            'country': ['exact', 'icontains'],
            'state': ['exact', 'icontains'],
            'city': ['exact', 'icontains'],
        }


class HospitalKYCRecordFilter(django_filters.FilterSet):
    """
    Filtering for Hospital KYC Records
    """
    hospital_name = django_filters.CharFilter(
        field_name='hospital__name',
        lookup_expr='icontains'
    )
    hospital_registration = django_filters.CharFilter(
        field_name='hospital__registration_number',
        lookup_expr='icontains'
    )
    status = django_filters.ChoiceFilter(choices=[
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REQUIRES_UPDATE', 'Requires Update'),
    ])

    # Date filters
    reviewed_after = django_filters.DateTimeFilter(field_name='reviewed_at', lookup_expr='gte')
    reviewed_before = django_filters.DateTimeFilter(field_name='reviewed_at', lookup_expr='lte')
    reviewed_on = django_filters.DateFilter(field_name='reviewed_at', lookup_expr='date')

    # Reviewer filters
    reviewed_by_username = django_filters.CharFilter(
        field_name='reviewed_by__username',
        lookup_expr='icontains'
    )
    reviewed_by = django_filters.NumberFilter(field_name='reviewed_by__id')

    # Reason search
    reason = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = HospitalKYCRecord
        fields = {
            'status': ['exact'],
            'hospital': ['exact'],
            'reviewed_by': ['exact'],
        }
