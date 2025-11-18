from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, RoomParticipant, GroupInvite
from .serializers import (
    ChatRoomSerializer,
    ChatRoomCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    UserSerializer,
    GroupInviteSerializer,
    GroupInviteCreateSerializer,
    DirectMessageCreateSerializer,
)
from .pagination import StandardResultsSetPagination, MessagePagination

User = get_user_model()


class ChatRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["room_type", "is_private"]

    def get_serializer_class(self):
        if self.action == "get_or_create_dm":
            return DirectMessageCreateSerializer
        if self.action in ["create", "update"]:
            return ChatRoomCreateSerializer
        return ChatRoomSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = (
            ChatRoom.objects.filter(
                roomparticipant__user=user, roomparticipant__is_active=True
            )
            .distinct()
            .prefetch_related(
                "roomparticipant_set__user",
                # 'roomparticipant_set__user.profile',
                "messages",
            )
            .select_related("created_by")
        )

        # Additional filtering by name (search)
        name = self.request.query_params.get("name", None)
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        room_serializer = ChatRoomSerializer(
            room, context=self.get_serializer_context()
        )
        return Response(room_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def get_or_create_dm(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_user_id = serializer.validated_data["user_id"]
        target_user = User.objects.get(id=target_user_id)

        existing_rooms = (
            ChatRoom.objects.filter(room_type="direct", participants=request.user)
            .filter(participants=target_user)
            .distinct()
        )

        if existing_rooms.exists():
            room = existing_rooms.first()
        else:
            room = ChatRoom.objects.create(
                room_type="direct", created_by=request.user, is_private=True
            )
            RoomParticipant.objects.create(room=room, user=request.user, role="member")
            RoomParticipant.objects.create(room=room, user=target_user, role="member")

        room_serializer = ChatRoomSerializer(room, context={"request": request})
        return Response(room_serializer.data)

    @action(detail=True, methods=["post"])
    def add_participant(self, request, pk=None):
        room = self.get_object()
        user_id = request.data.get("user_id")

        try:
            participant = RoomParticipant.objects.get(room=room, user=request.user)
            if participant.role not in ["admin", "moderator"]:
                return Response(
                    {"error": "You don't have permission to add participants"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except RoomParticipant.DoesNotExist:
            return Response(
                {"error": "You are not a participant of this room"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user_to_add = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if RoomParticipant.objects.filter(room=room, user=user_to_add).exists():
            return Response(
                {"error": "User is already a participant"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        RoomParticipant.objects.create(room=room, user=user_to_add, role="member")

        user_name = (
            user_to_add.profile.name
            if hasattr(user_to_add, "profile")
            else user_to_add.email
        )

        Message.objects.create(
            room=room,
            sender=request.user,
            content=f"{user_name} was added to the group",
            message_type="system",
        )

        return Response({"success": "User added to group"})

    @action(detail=True, methods=["post"])
    def remove_participant(self, request, pk=None):
        room = self.get_object()
        user_id = request.data.get("user_id")

        try:
            participant = RoomParticipant.objects.get(room=room, user=request.user)
            if participant.role not in ["admin", "moderator"]:
                return Response(
                    {
                        "error": "You don't have permission to remove participants"
                    },  # noqa
                    status=status.HTTP_403_FORBIDDEN,
                )
        except RoomParticipant.DoesNotExist:
            return Response(
                {"error": "You are not a participant of this room"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user_to_remove = User.objects.get(id=user_id)
            participant_to_remove = RoomParticipant.objects.get(
                room=room, user=user_to_remove
            )
        except (User.DoesNotExist, RoomParticipant.DoesNotExist):
            return Response(
                {"error": "User not found in this room"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if participant_to_remove.role == "admin" and participant.role != "admin":
            return Response(
                {"error": "Only admins can remove other admins"},
                status=status.HTTP_403_FORBIDDEN,
            )

        participant_to_remove.delete()

        user_name = (
            user_to_remove.profile.name
            if hasattr(user_to_remove, "profile")
            else user_to_remove.email
        )

        Message.objects.create(
            room=room,
            sender=request.user,
            content=f"{user_name} was removed from the group",
            message_type="system",
        )

        return Response({"success": "User removed from group"})

    @action(detail=True, methods=["post"])
    def leave_group(self, request, pk=None):
        room = self.get_object()

        if room.room_type != "group":
            return Response(
                {"error": "You can only leave group chats"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            participant = RoomParticipant.objects.get(room=room, user=request.user)
            participant.delete()

            user_name = (
                request.user.profile.name
                if hasattr(request.user, "profile")
                else request.user.email
            )

            Message.objects.create(
                room=room,
                sender=request.user,
                content=f"{user_name} left the group",
                message_type="system",
            )

            return Response({"success": "You have left the group"})

        except RoomParticipant.DoesNotExist:
            return Response(
                {"error": "You are not a participant of this room"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["patch"])
    def update_last_message(self, request, pk=None):
        room = self.get_object()
        last_message_data = request.data.get("last_message")

        if not last_message_data:
            return Response(
                {"error": "last_message is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update room's updated_at to reflect new activity
        room.updated_at = timezone.now()
        room.save()

        serializer = ChatRoomSerializer(room, context={"request": request})
        return Response(serializer.data)


class GroupInviteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["room", "is_active"]

    def get_serializer_class(self):
        if self.action == "create":
            return GroupInviteCreateSerializer
        return GroupInviteSerializer

    def get_queryset(self):
        user = self.request.user
        admin_rooms = ChatRoom.objects.filter(
            roomparticipant__user=user, roomparticipant__role__in=["admin", "moderator"]
        )
        return GroupInvite.objects.filter(Q(created_by=user) | Q(room__in=admin_rooms))


class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = MessagePagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "room",
        "message_type",
        "sender",
    ]

    def get_serializer_class(self):
        if self.action == "create":
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        room_id = self.request.query_params.get("room_id")
        if room_id:
            user_rooms = ChatRoom.objects.filter(
                roomparticipant__user=self.request.user
            )
            if user_rooms.filter(id=room_id).exists():
                queryset = Message.objects.filter(room_id=room_id).select_related(
                    "sender"
                )

                # Additional search by content
                search = self.request.query_params.get("search", None)
                if search:
                    queryset = queryset.filter(content__icontains=search)

                # Filter by date range
                date_from = self.request.query_params.get("date_from", None)
                date_to = self.request.query_params.get("date_to", None)
                if date_from:
                    queryset = queryset.filter(timestamp__gte=date_from)
                if date_to:
                    queryset = queryset.filter(timestamp__lte=date_to)

                return queryset.order_by("timestamp")
        return Message.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room_id = serializer.validated_data["room"].id
        user_rooms = ChatRoom.objects.filter(roomparticipant__user=request.user)
        if not user_rooms.filter(id=room_id).exists():
            return Response(
                {"error": "You don't have access to this chat room"},
                status=status.HTTP_403_FORBIDDEN,
            )

        message_data = {
            "room": serializer.validated_data["room"],
            "sender": request.user,
            "content": serializer.validated_data["content"],
            "message_type": serializer.validated_data.get("message_type", "text"),
        }

        reply_to_id = serializer.validated_data.get("reply_to_id")
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id, room=room_id)
                message_data["reply_to"] = reply_to
            except Message.DoesNotExist:
                pass

        message = Message.objects.create(**message_data)

        message_serializer = MessageSerializer(
            message, context=self.get_serializer_context()
        )
        return Response(message_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def mark_read(self, request):
        room_id = request.data.get("room_id")
        message_ids = request.data.get("message_ids", [])

        if not room_id or not message_ids:
            return Response(
                {"error": "room_id and message_ids are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify user has access to the room
        user_rooms = ChatRoom.objects.filter(roomparticipant__user=request.user)
        if not user_rooms.filter(id=room_id).exists():
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Mark messages as read
        messages = Message.objects.filter(id__in=message_ids, room_id=room_id)
        for message in messages:
            if request.user not in message.read_by.all():
                message.read_by.add(request.user)

        return Response({"success": f"Marked {len(messages)} messages as read"})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["email"]  # Filter by email

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id).prefetch_related(
            "chat_status"
        )

        # Search by name (from profile) or email
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(profile__name__icontains=search)
            )

        # Filter by online status
        online = self.request.query_params.get("online", None)
        if online is not None:
            online_bool = online.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(chat_status__online=online_bool)

        return queryset
