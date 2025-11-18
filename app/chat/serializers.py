from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, UserStatus, RoomParticipant, GroupInvite

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "name", "online", "photo", "last_seen"]

    def get_name(self, obj):
        return obj.profile.name if hasattr(obj, "profile") else obj.email

    def get_online(self, obj):
        try:
            return obj.chat_status.online
        except UserStatus.DoesNotExist:
            return False

    def get_photo(self, obj):
        try:
            return obj.profile.photo.url
        except Exception:
            return None

    def get_last_seen(self, obj):
        try:
            return obj.chat_status.last_seen
        except UserStatus.DoesNotExist:
            return None


class RoomParticipantSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = RoomParticipant
        fields = ["user", "role", "joined_at", "is_active"]

    def get_user(self, obj):
        return UserSerializer(obj.user).data


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "description",
            "room_type",
            "participants",
            "participant_count",
            "created_by",
            "is_private",
            "avatar",
            "created_at",
            "updated_at",
            "last_message",
            "unread_count",
            "user_role",
            "is_admin",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_participants(self, obj):
        participants = obj.roomparticipant_set.filter(is_active=True).select_related(
            "user"
        )[:10]
        return RoomParticipantSerializer(participants, many=True).data

    def get_participant_count(self, obj):
        return obj.roomparticipant_set.filter(is_active=True).count()

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message, context=self.context).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.messages.exclude(read_by=request.user).count()
        return 0

    def get_user_role(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                participant = RoomParticipant.objects.get(room=obj, user=request.user)
                return participant.role
            except RoomParticipant.DoesNotExist:
                return None
        return None

    def get_is_admin(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                participant = RoomParticipant.objects.get(room=obj, user=request.user)
                return participant.role in ["admin", "moderator"]
            except RoomParticipant.DoesNotExist:
                return False
        return False


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = ChatRoom
        fields = ["name", "description", "room_type", "is_private", "participant_ids"]

    def create(self, validated_data):
        participant_ids = validated_data.pop("participant_ids", [])
        request = self.context.get("request")

        room = ChatRoom.objects.create(created_by=request.user, **validated_data)

        if validated_data["room_type"] == "group":
            RoomParticipant.objects.create(room=room, user=request.user, role="admin")
        else:
            RoomParticipant.objects.create(room=room, user=request.user, role="member")

        for user_id in participant_ids:
            try:
                user = User.objects.get(id=user_id)
                if user != request.user:
                    RoomParticipant.objects.create(room=room, user=user, role="member")
            except User.DoesNotExist:
                continue

        return room


class DirectMessageCreateSerializer(serializers.Serializer):
    user_id = serializers.CharField(required=True)

    def validate_user_id(self, value):
        """Validate that the user exists and is not the current user"""
        request = self.context.get("request")

        if value == request.user.id:
            raise serializers.ValidationError("Cannot create DM with yourself")

        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        return value


class GroupInviteSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source="room.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = GroupInvite
        fields = [
            "id",
            "code",
            "room",
            "room_name",
            "created_by",
            "created_by_name",
            "max_uses",
            "used_count",
            "expires_at",
            "is_active",
            "is_valid",
            "created_at",
        ]
        read_only_fields = ["id", "code", "used_count", "created_at"]

    def get_created_by_name(self, obj):
        return (
            obj.created_by.profile.name
            if hasattr(obj.created_by, "profile")
            else obj.created_by.email
        )


class GroupInviteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupInvite
        fields = ["max_uses", "expires_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    is_own_message = serializers.SerializerMethodField()
    reply_to = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "room",
            "sender",
            "content",
            "message_type",
            "file",
            "timestamp",
            "is_own_message",
            "reply_to",
        ]
        read_only_fields = ["id", "timestamp", "sender"]

    def get_is_own_message(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.sender == request.user
        return False

    def get_reply_to(self, obj):
        if obj.reply_to:
            return MessageSerializer(obj.reply_to, context=self.context).data
        return None


class MessageCreateSerializer(serializers.ModelSerializer):
    reply_to_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Message
        fields = ["content", "room", "message_type", "file", "reply_to_id"]
