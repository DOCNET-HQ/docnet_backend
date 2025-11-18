from meet.models import Meet
from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()


class MeetSerializer(serializers.ModelSerializer):
    """Serializer for the Meet model."""

    class Meta:
        model = Meet
        fields = [
            "id",
            "channel_name",
            "created_at",
        ]


class BasicMeetSerializer(serializers.ModelSerializer):
    """Basic Serializer for the Meet model."""

    class Meta:
        model = Meet
        fields = [
            "id",
        ]


class MeetTokenCreateSerializer(serializers.Serializer):
    """Serializer for creating a Meet token."""

    channel_name = serializers.CharField(max_length=255)


class MeetTokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=500)
    expires_in = serializers.IntegerField()


class MeetMembersSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="profile.name", read_only=True)
    photo = serializers.SerializerMethodField()

    def get_photo(self, obj):
        try:
            return obj.profile.photo.url
        except ValueError:
            return None

    class Meta:
        model = User
        fields = ["name", "photo", "role"]


class MeetCalendarSerializer(serializers.ModelSerializer):
    meet_id = serializers.CharField(source="id", read_only=True)
    appointment_id = serializers.SerializerMethodField(required=False, read_only=True)
    reason = serializers.SerializerMethodField(required=False, read_only=True)
    notes = serializers.SerializerMethodField(required=False, read_only=True)
    start_datetime = serializers.SerializerMethodField(required=False, read_only=True)
    end_datetime = serializers.SerializerMethodField(required=False, read_only=True)
    is_appointment = serializers.SerializerMethodField()
    members = MeetMembersSerializer(many=True, read_only=True)

    class Meta:
        model = Meet
        fields = [
            "meet_id",
            "is_appointment",
            "appointment_id",
            "reason",
            "notes",
            "start_datetime",
            "end_datetime",
            "members",
        ]

    def get_is_appointment(self, obj):
        return obj.appointment is not None

    def get_appointment_id(self, obj):
        if obj.appointment:
            return obj.appointment.id
        else:
            return ""

    def get_reason(self, obj):
        if obj.appointment:
            return obj.appointment.reason
        else:
            return ""

    def get_notes(self, obj):
        if obj.appointment:
            return obj.appointment.notes
        else:
            return ""

    def get_start_datetime(self, obj):
        if obj.appointment:
            return obj.appointment.scheduled_start_time
        else:
            return ""

    def get_end_datetime(self, obj):
        if obj.appointment:
            return obj.appointment.scheduled_end_time
        else:
            return ""
