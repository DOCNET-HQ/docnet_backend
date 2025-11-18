from meet.models import Meet
from django.contrib import admin


@admin.register(Meet)
class MeetAdmin(admin.ModelAdmin):
    """
    Admin interface for Meet model
    """

    list_display = [
        "id",
        "channel_name",
        "created_at",
        "updated_at",
    ]

    search_fields = [
        "id",
        "channel_name",
    ]

    readonly_fields = [
        "id",
        "channel_name",
        "created_at",
        "updated_at",
    ]

    date_hierarchy = "created_at"

    list_per_page = 25
