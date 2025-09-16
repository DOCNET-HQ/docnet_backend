from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Hospital, HospitalKYCRecord

User = get_user_model()


class HospitalSerializer(serializers.ModelSerializer):
    """
    Serializer for Hospital model with all fields
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Hospital
        fields = [
            'id', 'user', 'email', 'user_username', 'name', 'dob',
            'phone_number', 'website', 'bio', 'photo', 'address', 'country',
            'state', 'city', 'postal_code', 'id_document', 'kyc_status', 'is_visible',
            'is_active', 'registration_number', 'license_name',
            'license_issuance_authority', 'license_number', 'license_issue_date',
            'license_expiry_date', 'license_document', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'email', 'user_username']
        extra_kwargs = {
            'user': {'write_only': True},
        }

    def validate_license_expiry_date(self, value):
        """
        Validate that license expiry date is not in the past
        """
        if value and self.instance:
            from django.utils import timezone
            if value < timezone.now().date():
                raise serializers.ValidationError(
                    "License expiry date cannot be in the past."
                )
        return value

    def validate_phone_number(self, value):
        """
        Validate phone number format
        """
        if value:
            # Remove any spaces or special characters for validation
            clean_number = ''.join(filter(str.isdigit, value))
            if len(clean_number) < 10 or len(clean_number) > 15:
                raise serializers.ValidationError(
                    "Phone number must be between 10 and 15 digits."
                )
        return value


class HospitalCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Hospital instances
    """
    class Meta:
        model = Hospital
        fields = [
            'name', 'dob', 'phone_number', 'website', 'bio', 'photo',
            'address', 'country', 'state', 'city', 'postal_code', 'is_visible',
            'id_document', 'registration_number', 'license_name',
            'license_issuance_authority', 'license_number', 'license_issue_date',
            'license_expiry_date', 'license_document'
        ]

    def create(self, validated_data):
        """
        Create hospital profile with associated user
        """
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class HospitalUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Hospital instances
    """
    class Meta:
        model = Hospital
        fields = [
            'name', 'dob', 'phone_number', 'website', 'bio', 'photo',
            'address', 'country', 'state', 'city', 'postal_code', 'is_visible',
            'id_document', 'registration_number', 'license_name',
            'license_issuance_authority', 'license_number', 'license_issue_date',
            'license_expiry_date', 'license_document', 'is_visible'
        ]


class HospitalListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing hospitals
    """
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'phone_number', 'website', 'address', 'city',
            'state', 'country', 'kyc_status', 'is_active', 'is_visible', 'email',
            'registration_number', 'license_number', 'license_expiry_date',
            'created_at', 'updated_at'
        ]


class HospitalKYCRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for Hospital KYC Record model
    """
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    reviewed_by_email = serializers.EmailField(source='reviewed_by.email', read_only=True)

    class Meta:
        model = HospitalKYCRecord
        fields = [
            'id', 'hospital', 'hospital_name', 'status', 'reason',
            'reviewed_by', 'reviewed_by_username', 'reviewed_by_email',
            'reviewed_at'
        ]
        read_only_fields = ['id', 'reviewed_at', 'hospital_name',
                           'reviewed_by_username', 'reviewed_by_email']

    def validate(self, data):
        """
        Validate KYC record data
        """
        if data.get('status') in ['REJECTED', 'REQUIRES_UPDATE'] and not data.get('reason'):
            raise serializers.ValidationError({
                'reason': 'Reason is required when status is REJECTED or REQUIRES_UPDATE'
            })
        return data


class HospitalKYCRecordCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Hospital KYC Records
    """
    class Meta:
        model = HospitalKYCRecord
        fields = ['hospital', 'status', 'reason']

    def create(self, validated_data):
        """
        Create KYC record with reviewer information
        """
        validated_data['reviewed_by'] = self.context['request'].user
        return super().create(validated_data)


class HospitalKYCRecordUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Hospital KYC Records
    """
    class Meta:
        model = HospitalKYCRecord
        fields = ['status', 'reason']

    def update(self, instance, validated_data):
        """
        Update KYC record with new reviewer information
        """
        validated_data['reviewed_by'] = self.context['request'].user
        return super().update(instance, validated_data)
