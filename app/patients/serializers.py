from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Patient, PatientKYCRecord, PatientEmergencyContact

User = get_user_model()


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for Patient model with all fields
    """
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id', 'user', 'email', 'name', 'dob', 'phone_number', 'website',
            'bio', 'photo', 'address', 'country', 'state', 'city',
            'postal_code', 'id_document', 'kyc_status', 'is_visible',
            'is_active', 'gender', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'email']
        extra_kwargs = {
            'user': {'write_only': True},
        }

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


class BasicPatientSerializer(serializers.ModelSerializer):
    """
    Serializer to get Patient Basic Info
    """
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id', 'email', 'name', 'photo',
        ]
        read_only_fields = [
            'id', 'email', 'name', 'photo',
        ]


class PatientCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Patient instances
    """
    class Meta:
        model = Patient
        fields = [
            'name', 'dob', 'phone_number', 'website', 'bio', 'photo',
            'address', 'country', 'state', 'city', 'postal_code',
            'id_document', 'kyc_status', 'is_visible', 'is_active', 'gender'
        ]

    def create(self, validated_data):
        """
        Create Patient profile with associated user
        """
        email = self.context['request'].data.get('email')
        user, created = User.objects.get_or_create(email=email)
        validated_data['user'] = user
        return super().create(validated_data)


class PatientUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Patient instances
    """
    class Meta:
        model = Patient
        fields = [
            'name', 'dob', 'phone_number', 'website', 'bio', 'photo',
            'address', 'country', 'state', 'city', 'postal_code',
            'id_document', 'kyc_status', 'is_visible', 'is_active', 'gender'
        ]


class PatientListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing Patients
    """
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id', 'name', 'phone_number', 'website', 'address', 'city',
            'state', 'country', 'kyc_status', 'is_active', 'is_visible',
            'email', 'created_at', 'updated_at'
        ]


class PatientKYCRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for Patient KYC Record model
    """
    patient_name = serializers.CharField(
        source='patient.name', read_only=True
    )
    reviewed_by_email = serializers.EmailField(
        source='reviewed_by.email', read_only=True
    )

    class Meta:
        model = PatientKYCRecord
        fields = [
            'id', 'patient', 'patient_name', 'status', 'reason',
            'reviewed_by', 'reviewed_by_email', 'reviewed_at'
        ]
        read_only_fields = [
            'id', 'reviewed_at', 'patient_name', 'reviewed_by_email'
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


class PatientKYCRecordCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Patient KYC Records
    """
    class Meta:
        model = PatientKYCRecord
        fields = ['patient', 'status', 'reason']

    def create(self, validated_data):
        """
        Create KYC record with reviewer information
        """
        validated_data['reviewed_by'] = self.context['request'].user
        return super().create(validated_data)


class PatientKYCRecordUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Patient KYC Records
    """
    class Meta:
        model = PatientKYCRecord
        fields = ['status', 'reason']

    def update(self, instance, validated_data):
        """
        Update KYC record with new reviewer information
        """
        validated_data['reviewed_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class PatientEmergencyContactSerializer(serializers.ModelSerializer):
    """
    Serializer for Patient Emergency Contact model
    """
    class Meta:
        model = PatientEmergencyContact
        fields = [
            'id', 'patient', 'name', 'relationship', 'phone_number', 'email',
            'address', 'preferred_contact_method'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        """
        Validate that patient doesn't exceed 2 emergency contacts
        """
        patient = data.get('patient')
        if patient and self.instance:
            # For updates, exclude current instance from count
            existing_count = patient.emergency_contacts.exclude(
                id=self.instance.id
            ).count()
        elif patient:
            # For creation, count all existing contacts
            existing_count = patient.emergency_contacts.count()
        else:
            existing_count = 0

        if existing_count >= 2:
            raise serializers.ValidationError({
                'patient': 'A patient cannot have more than 2 emergency contacts.' # noqa
            })
        return data


class PatientEmergencyContactCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Patient Emergency Contacts
    """
    class Meta:
        model = PatientEmergencyContact
        fields = [
            'patient', 'name', 'relationship', 'phone_number', 'email',
            'address', 'preferred_contact_method'
        ]

    def validate(self, data):
        """
        Validate that patient doesn't exceed 2 emergency contacts
        """
        patient = data.get('patient')
        if patient and patient.emergency_contacts.count() >= 2:
            raise serializers.ValidationError({
                'patient': 'A patient cannot have more than 2 emergency contacts.' # noqa
            })
        return data
