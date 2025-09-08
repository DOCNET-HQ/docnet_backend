from django.conf import settings
from users.choices import USER_ROLES
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import InvalidToken


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the user object
    """
    role = serializers.ChoiceField(choices=(
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('hospital', 'Hospital'),
    ))
    name = serializers.CharField(max_length=100, write_only=True)
    country = serializers.CharField(max_length=100, write_only=True)
    state = serializers.CharField(max_length=100, write_only=True)
    city = serializers.CharField(max_length=100, write_only=True)
    phone_number = serializers.CharField(max_length=15, write_only=True)

    class Meta:
        model = get_user_model()
        exclude = (
            "groups",
            "is_staff",
            "is_active",
            "last_login",
            "is_superuser",
            "date_modified",
            "user_permissions",
        )
        required_fields = [
            "email",
            "password",
            "role",
            "name",
            "country",
            "phone_number",
        ]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 5},
        }

    def create(self, validated_data):
        """
        Create a user with encrypted password and corresponding profile
        """
        # Extract profile data
        name = validated_data.pop('name')
        country = validated_data.pop('country')
        state = validated_data.pop('state')
        city = validated_data.pop('city')
        phone_number = validated_data.pop('phone_number')
        # Keep role in validated_data for user creation
        role = validated_data.get('role')

        # Create user
        user = get_user_model().objects.create_user(
            **validated_data, is_active=False
        )

        # Create the appropriate profile based on role
        if role == 'patient':
            # Import here to avoid circular imports
            from patients.models import Patient
            Patient.objects.create(
                user=user,
                name=name,
                country=country,
                state=state,
                city=city,
                phone_number=phone_number
            )
        elif role == 'doctor':
            # Import here to avoid circular imports
            from doctors.models import Doctor
            Doctor.objects.create(
                user=user,
                name=name,
                country=country,
                state=state,
                city=city,
                phone_number=phone_number
            )
        elif role == 'hospital':
            # Import here to avoid circular imports
            from hospitals.models import Hospital
            Hospital.objects.create(
                user=user,
                name=name,
                country=country,
                state=state,
                city=city,
                phone_number=phone_number
            )
        # No profile creation for admin role

        return user

    def update(self, instance, validated_data):
        """
        Update a user, setting the password correctly and return it
        """
        # Remove profile fields from validated_data if present
        profile_fields = ['name', 'country', 'state', 'city', 'phone_number']
        profile_data = {}

        for field in profile_fields:
            if field in validated_data:
                profile_data[field] = validated_data.pop(field)

        # Update user instance
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        # Update profile if profile data provided
        if profile_data:
            for key, value in profile_data.items():
                setattr(user.profile, key, value)
            user.profile.save()

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"] = serializers.CharField(write_only=True)
        self.fields["photo"] = serializers.CharField(read_only=True)
        self.fields["name"] = serializers.CharField(read_only=True)
        self.fields["email"] = serializers.CharField()

    def validate(self, attrs):
        input_role = attrs.pop("role", None)
        if not input_role:
            raise ValidationError({"role": "This field is required."})

        # Check if the user's account is active
        user_ = User.objects.filter(email=attrs["email"]).first()

        if not user_:
            raise ValidationError(
                {
                    "email": "User with this email does not exist.",
                    "code": "user_not_found"
                }
            )

        if not user_.is_active:
            raise ValidationError(
                {
                    "email": "You need to verify your email.",
                    "code": "account_not_activated"
                },
            )

        if not user_.check_password(attrs["password"]):
            raise ValidationError(
                {
                    "password": "Incorrect password.",
                    "code": "incorrect_password"
                }
            )

        # Validate email and password
        data = super().validate(attrs)

        if input_role not in list(zip(*USER_ROLES))[0]:
            raise ValidationError(
                {"role": f"{input_role} is an Invalid role."}
            )

        # Check if the user's role matches the provided role
        if self.user.role != input_role:
            raise ValidationError(
                {
                    "role": f"{self.user.role} cannot login on the {input_role} portal." # noqa
                }
            )

        if self.user.role == 'admin' and not self.user.is_staff:
            raise ValidationError(
                {
                    "password": "You have not been added as a staff.",
                    "code": "staff_access_required"
                }
            )

        data["user"] = {}

        if (
            hasattr(self.user, "profile") and
            self.user.profile is not None and
            self.user.profile.photo
        ):
            data["user"]["photo"] = self.user.profile.photo.url
        else:
            data["user"]["photo"] = ""

        data["user"]["email"] = self.user.email
        data["user"]["user_id"] = self.user.id
        data["user"]["role"] = self.user.role

        if self.user.profile is not None:
            data["user"]["name"] = self.user.profile.name
            data["user"]["profile_id"] = self.user.profile.id
            if self.user.role != "admin":
                data["user"]["kyc_status"] = self.user.profile.kyc_status
        else:
            data["user"]["name"] = self.user.email.split("@")[0]
            data["user"]["profile_id"] = None
            if self.user.role != "admin":
                data["user"]["kyc_status"] = None

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token


class JWTCookieTokenRefreshSerializer(TokenRefreshSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["refresh"] = serializers.CharField(write_only=True)

    refresh = None

    def validate(self, attrs):
        attrs["refresh"] = attrs.get(settings.SIMPLE_JWT["REFRESH_TOKEN_NAME"])

        if attrs["refresh"]:
            return super().validate(attrs)
        else:
            raise InvalidToken("No valid refresh token found")


class AccountActivationSerializer(serializers.Serializer):
    pass


class LogOutSerializer(serializers.Serializer):
    pass


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)
