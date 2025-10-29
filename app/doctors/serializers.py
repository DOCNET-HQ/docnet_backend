from utils.choices import GENDER
from rest_framework import serializers
from .models import Doctor, DoctorKYCRecord
from django.contrib.auth import get_user_model
from users.password_service import PasswordService
from users.email_services import EmailService

User = get_user_model()
email_service = EmailService()


class DoctorSerializer(serializers.ModelSerializer):
    """
    Serializer for Doctor model with all fields
    """
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id', 'hospital', 'user', 'email', 'name', 'dob',
            'phone_number', 'website', 'bio', 'photo', 'address', 'country',
            'state', 'city', 'postal_code', 'id_document', 'kyc_status',
            'is_visible', 'is_active', 'gender', 'specialty', 'degree',
            'years_of_experience', 'license_name', 'license_issuance_authority', 
            'license_number', 'license_issue_date', 'license_expiry_date', 
            'license_document', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'email']
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


class BasicDoctorSerializer(serializers.ModelSerializer):
    """
    Serializer to get Doctor Basic Info
    """
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id', 'email', 'name', 'photo',
        ]
        read_only_fields = [
            'id', 'email', 'name', 'photo',
        ]


class DoctorCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Doctor instances
    """
    email = serializers.EmailField(required=True, write_only=True)
    name = serializers.CharField(required=True)
    gender = serializers.ChoiceField(choices=GENDER, required=True)
    phone_number = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    specialty = serializers.CharField(required=True)
    
    class Meta:
        model = Doctor
        fields = [
            'email', 'name', 'dob', 'phone_number', 'website', 'bio', 'photo', 
            'address', 'country', 'state', 'city', 'postal_code', 
            'id_document', 'kyc_status', 'is_visible', 'is_active', 'gender', 
            'specialty', 'degree', 'years_of_experience', 'license_name', 
            'license_issuance_authority', 'license_number', 'license_issue_date', 
            'license_expiry_date', 'license_document',
        ]

    def create(self, validated_data):
        """
        Create Doctor profile with associated user
        """
        email = validated_data.pop('email')

        user, created = PasswordService.create_user_with_password_setup(
            email=email,
            role='doctor'
        )

        if not user.role == 'doctor':
            raise serializers.ValidationError(
                {
                    "email": "This user has a profile and they are not a doctor."
                }
            )

        # We will later do this in a way that users can /
        #  have mulpitle doctor profiles but only one can be active
        if hasattr(user, 'doctor_profile'):
            raise serializers.ValidationError(
                {"email": "A doctor profile with this email already exists."}
            )

        # If user was newly created, send password setup email
        if created:
            email_service.send_welcome_email(user)

            PasswordService.send_password_setup_email(
                self.context['request'], 
                user
            )

        validated_data['user'] = user
        return super().create(validated_data)


class DoctorUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Doctor instances
    """
    class Meta:
        model = Doctor
        fields = [
            'name', 'dob', 'phone_number', 'website', 'bio', 'photo', 
            'address', 'country', 'state', 'city', 'postal_code', 
            'id_document', 'kyc_status', 'is_visible', 'is_active', 'gender', 
            'specialty', 'degree', 'years_of_experience', 'license_name', 
            'license_issuance_authority', 'license_number', 'license_issue_date', 
            'license_expiry_date', 'license_document',
        ]


class DoctorListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing Doctors
    """
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id', 'name', 'phone_number', 'photo', 'website', 'address', 'city',
            'state', 'country', 'kyc_status', 'is_active', 'is_visible',
            'specialty', 'email', 'license_number', 'kyc_status',
            'license_expiry_date', 'created_at', 'updated_at'
        ]


class DoctorKYCRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for Doctor KYC Record model
    """
    doctor_name = serializers.CharField(
        source='doctor.name', read_only=True
    )
    reviewed_by_email = serializers.EmailField(
        source='reviewed_by.email', read_only=True
    )

    class Meta:
        model = DoctorKYCRecord
        fields = [
            'id', 'doctor', 'doctor_name', 'status', 'reason',
            'reviewed_by', 'reviewed_by_email',
            'reviewed_at'
        ]
        read_only_fields = [
            'id', 'reviewed_at', 'doctor_name', 'reviewed_by_email'
        ]

    def validate(self, data):
        """
        Validate KYC record data
        """
        if data.get('status') in ['REJECTED', 'REQUIRES_UPDATE'] and not data.get('reason'): # noqa
            raise serializers.ValidationError({
                'reason': 'Reason is required when status is REJECTED or REQUIRES_UPDATE' # noqa
            })
        return data


class DoctorKYCRecordCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Doctor KYC Records
    """
    class Meta:
        model = DoctorKYCRecord
        fields = ['doctor', 'status', 'reason']

    def create(self, validated_data):
        """
        Create KYC record with reviewer information
        """
        validated_data['reviewed_by'] = self.context['request'].user
        return super().create(validated_data)


class DoctorKYCRecordUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Doctor KYC Records
    """
    class Meta:
        model = DoctorKYCRecord
        fields = ['status', 'reason']

    def update(self, instance, validated_data):
        """
        Update KYC record with new reviewer information
        """
        validated_data['reviewed_by'] = self.context['request'].user
        return super().update(instance, validated_data)
