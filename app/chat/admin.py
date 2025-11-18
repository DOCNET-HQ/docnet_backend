from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import ChatRoom, RoomParticipant, Message, UserStatus, GroupInvite

User = get_user_model()


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "room_type",
        "created_by",
        "is_private",
        "created_at",
        "updated_at",
    )
    list_filter = ("room_type", "is_private", "created_at", "updated_at")
    search_fields = ("id", "name", "description", "created_by__email")
    readonly_fields = ("id", "created_at", "updated_at")
    # filter_horizontal = ('participants',)

    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("id", "name", "description", "room_type", "avatar")},
        ),
        (_("Privacy & Ownership"), {"fields": ("is_private", "created_by")}),
        # (_('Participants'), {
        #     'fields': ('participants',)
        # }),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(RoomParticipant)
class RoomParticipantAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "role", "is_active", "joined_at")
    list_filter = ("role", "is_active", "joined_at", "room__room_type")
    search_fields = ("room__name", "room__id", "user__email", "user__profile__name")
    readonly_fields = ("joined_at",)

    fieldsets = (
        (_("Membership Details"), {"fields": ("room", "user", "role")}),
        (_("Status"), {"fields": ("is_active", "joined_at")}),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "room",
        "sender",
        "message_type",
        "timestamp",
        "truncated_content",
    )
    list_filter = ("message_type", "timestamp", "room__room_type")
    search_fields = ("content", "room__name", "sender__email", "sender__profile__name")
    readonly_fields = ("timestamp",)
    date_hierarchy = "timestamp"

    fieldsets = (
        (
            _("Message Content"),
            {
                "fields": (
                    "room",
                    "sender",
                    "content",
                    "message_type",
                    "file",
                    "reply_to",
                )
            },
        ),
        (_("Metadata"), {"fields": ("timestamp", "read_by"), "classes": ("collapse",)}),
    )

    def truncated_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    truncated_content.short_description = "Content"


@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ("user", "online", "last_seen")
    list_filter = ("online", "last_seen")
    search_fields = ("user__email", "user__profile__name")
    readonly_fields = ("last_seen",)

    fieldsets = (
        (_("User Information"), {"fields": ("user",)}),
        (_("Status Information"), {"fields": ("online", "last_seen")}),
    )


@admin.register(GroupInvite)
class GroupInviteAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "room",
        "created_by",
        "is_active",
        "is_valid",
        "created_at",
        "expires_at",
    )
    list_filter = ("is_active", "created_at", "expires_at")
    search_fields = ("code", "room__name", "created_by__email")
    readonly_fields = ("code", "used_count", "created_at")

    fieldsets = (
        (_("Invite Details"), {"fields": ("code", "room", "created_by")}),
        (_("Usage Limits"), {"fields": ("max_uses", "used_count", "expires_at")}),
        (_("Status"), {"fields": ("is_active", "created_at")}),
    )

    def is_valid(self, obj):
        return obj.is_valid()

    is_valid.boolean = True
    is_valid.short_description = "Valid"


class RoomParticipantInline(admin.TabularInline):
    model = RoomParticipant
    extra = 1
    readonly_fields = ("joined_at",)
    fields = ("user", "role", "is_active", "joined_at")


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("timestamp",)
    fields = ("sender", "content", "message_type", "timestamp")
    show_change_link = True


ChatRoomAdmin.inlines = [RoomParticipantInline, MessageInline]
