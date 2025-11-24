from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import shortuuid

User = get_user_model()


def generate_short_uuid():
    return shortuuid.uuid()


class ChatRoom(models.Model):
    ROOM_TYPES = (
        ("direct", "Direct Message"),
        ("group", "Group Chat"),
        ("video_call", "Video Call"),
    )

    id = models.CharField(max_length=30, primary_key=True, default=generate_short_uuid)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    room_type = models.CharField(max_length=30, choices=ROOM_TYPES, default="direct")
    participants = models.ManyToManyField(
        User, related_name="chat_rooms", through="RoomParticipant"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_rooms"
    )
    is_private = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="chat_avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        if self.name:
            return self.name

        if self.room_type == "direct":
            participants = self.participants.exclude(id=self.created_by_id)[:2]
            names = []

            for user in participants:
                try:
                    names.append(user.profile.name)
                except Exception:
                    # fallback if no profile
                    names.append(user.email)

            return f"DM: {', '.join(names)}"

        return f"Group: {self.id}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = shortuuid.uuid()
        super().save(*args, **kwargs)


class RoomParticipant(models.Model):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("moderator", "Moderator"),
        ("member", "Member"),
    )

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["room", "user"]


class Message(models.Model):
    MESSAGE_TYPES = (
        ("text", "Text"),
        ("system", "System Message"),
        ("image", "Image"),
        ("file", "File"),
    )

    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=10, choices=MESSAGE_TYPES, default="text"
    )
    file = models.FileField(upload_to="chat_files/", blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    read_by = models.ManyToManyField(User, related_name="read_messages", blank=True)
    reply_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies"
    )

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        sender_name = (
            self.sender.profile.name
            if hasattr(self.sender, "profile")
            else self.sender.email
        )
        return f"{sender_name}: {self.content[:50]}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        # Only add to read_by AFTER saving
        if is_new and self.sender:
            self.read_by.add(self.sender)


class UserStatus(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="chat_status"
    )
    online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_name = (
            self.user.profile.name
            if hasattr(self.user, "profile")
            else self.user.email  # noqa
        )
        status = "Online" if self.online else "Offline"
        return f"{user_name} - {status}"


class GroupInvite(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="invites")
    code = models.CharField(max_length=50, unique=True, default=generate_short_uuid)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_invites"
    )
    max_uses = models.PositiveIntegerField(default=1, help_text="0 for unlimited uses")
    used_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        return True

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = shortuuid.uuid()
        super().save(*args, **kwargs)
