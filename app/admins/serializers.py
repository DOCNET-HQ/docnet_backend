from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AdminProfile

User = get_user_model()


class AdminSerializer(serializers.ModelSerializer):
    """
    Serializer for AdminProfile model with all fields
    """
    email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    is_active = serializers.BooleanField(
        source='user.is_active',
        read_only=True
    )

    class Meta:
        model = AdminProfile
        fields = [
            'id', 'user', 'email', 'name', 'phone_number',
            'photo', 'country', 'state', 'city', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'email', 'is_active'
        ]
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


class BasicAdminSerializer(serializers.ModelSerializer):
    """
    Serializer to get AdminProfile Basic Info
    """
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AdminProfile
        fields = [
            'id', 'email', 'name', 'photo',
        ]
        read_only_fields = [
            'id', 'email', 'name', 'photo',
        ]


class AdminUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating AdminProfile instances
    """
    class Meta:
        model = AdminProfile
        fields = [
            'name', 'phone_number', 'photo',
            'country', 'state', 'city',
        ]


class AdminListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing admins
    """
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AdminProfile
        fields = [
            'id', 'name', 'phone_number', 'email', 'photo',
            'country', 'state', 'city',
        ]
