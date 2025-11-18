from doctors.models import Doctor
from hospitals.models import Hospital
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DoctorReview, HospitalReview

User = get_user_model()


class ReviewUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    name = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    def get_name(self, obj):
        try:
            return obj.profile.name
        except Exception:
            return obj.email

    def get_photo(self, obj):
        try:
            return obj.profile.photo.url
        except Exception:
            return None


class ReviewBaseSerializer(serializers.ModelSerializer):
    user = ReviewUserSerializer(read_only=True)
    is_auth_user = serializers.SerializerMethodField()
    is_updated = serializers.SerializerMethodField()

    class Meta:
        fields = (
            "id",
            "user",
            "rating",
            "text",
            "created_at",
            "updated_at",
            "is_auth_user",
            "is_updated",
        )
        read_only_fields = ("user", "created_at", "updated_at")

    def get_is_auth_user(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

    def get_is_updated(self, obj):
        return obj.is_updated


class DoctorReviewSerializer(ReviewBaseSerializer):
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)

    class Meta(ReviewBaseSerializer.Meta):
        model = DoctorReview
        fields = ReviewBaseSerializer.Meta.fields + ("doctor", "doctor_name")


class HospitalReviewSerializer(ReviewBaseSerializer):
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)

    class Meta(ReviewBaseSerializer.Meta):
        model = HospitalReview
        fields = ReviewBaseSerializer.Meta.fields + ("hospital", "hospital_name")


class DoctorReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorReview
        fields = ("rating", "text")

    def validate(self, attrs):
        request = self.context.get("request")
        view = self.context.get("view")

        doctor_id = view.kwargs.get("doctor_id")
        if not doctor_id:
            raise serializers.ValidationError("Doctor ID not found in URL.")

        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Doctor does not exist.")

        # Check if user already reviewed this doctor
        if request.user.is_authenticated:
            if DoctorReview.objects.filter(user=request.user, doctor=doctor).exists():
                raise serializers.ValidationError(
                    "You have already reviewed this doctor."
                )

        attrs["doctor"] = doctor
        return attrs


class HospitalReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalReview
        fields = ("rating", "text")

    def validate(self, attrs):
        request = self.context.get("request")
        view = self.context.get("view")

        hospital_id = view.kwargs.get("hospital_id")
        if not hospital_id:
            raise serializers.ValidationError("Hospital ID not found in URL.")

        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            raise serializers.ValidationError("Hospital does not exist.")

        # Check if user already reviewed this hospital
        if request.user.is_authenticated:
            if HospitalReview.objects.filter(
                user=request.user, hospital=hospital
            ).exists():
                raise serializers.ValidationError(
                    "You have already reviewed this hospital."
                )

        attrs["hospital"] = hospital
        return attrs
