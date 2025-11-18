from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from .models import Appointment
from .choices import AppointmentStatus, CancelledBy


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Appointment model with organized fieldsets
    """

    list_display = [
        "id_short",
        "appointment_type",
        "status_badge",
        "scheduled_start_time",
        "timezone",
        "is_upcoming_badge",
        "meet_display",
        "created_at",
    ]

    list_filter = [
        "status",
        "appointment_type",
        "timezone",
        "scheduled_start_time",
        "created_at",
        "cancelled_by",
    ]

    search_fields = [
        "id",
        "patient__user__name",
        "patient__user__email",
        "doctor__user__name",
        "reason",
        "notes",
        "meet__id",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "duration_display",
        "is_upcoming_display",
        "is_past_display",
        "meet_display",
    ]

    raw_id_fields = ["meet"]

    date_hierarchy = "scheduled_start_time"

    list_per_page = 25

    ordering = ["-scheduled_start_time"]

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": ("id", "patient", "doctor", "created_by"),
                "description": _("Core appointment identification details"),
            },
        ),
        (
            _("Appointment Details"),
            {
                "fields": ("appointment_type", "status", "reason", "notes"),
                "description": _("Information about the appointment type and purpose"),
            },
        ),
        (
            _("Schedule Information"),
            {
                "fields": (
                    "scheduled_start_time",
                    "scheduled_end_time",
                    "timezone",
                    "duration_display",
                    "is_upcoming_display",
                    "is_past_display",
                ),
                "description": _("Appointment timing and schedule details"),
            },
        ),
        (
            _("Telemedicine Details"),
            {
                "fields": (
                    "meet",
                    "meet_display",
                    "technical_issues_reported",
                ),
                "classes": ("collapse",),
                "description": _("Video conferencing and technical information"),
            },
        ),
        (
            _("Cancellation Information"),
            {
                "fields": ("cancellation_reason", "cancelled_by"),
                "classes": ("collapse",),
                "description": _("Details if appointment was cancelled"),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
                "description": _("System timestamps"),
            },
        ),
    )

    # Custom methods for display
    @admin.display(description="ID", ordering="id")
    def id_short(self, obj):
        """Display shortened UUID"""
        return str(obj.id)[:8]

    @admin.display(description="Status")
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            "scheduled": "#ffc107",  # amber
            "confirmed": "#17a2b8",  # cyan
            "in_progress": "#007bff",  # blue
            "completed": "#28a745",  # green
            "cancelled": "#dc3545",  # red
            "no_show": "#6c757d",  # gray
            "rescheduled": "#fd7e14",  # orange
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',  # noqa
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Upcoming", boolean=True)
    def is_upcoming_badge(self, obj):
        """Display if appointment is upcoming"""
        return obj.is_upcoming

    @admin.display(description="Duration")
    def duration_display(self, obj):
        """Display appointment duration"""
        if obj.duration:
            return str(obj.duration)
        return "-"

    @admin.display(description="Is Upcoming", boolean=True)
    def is_upcoming_display(self, obj):
        """Display if upcoming"""
        return obj.is_upcoming

    @admin.display(description="Is Past", boolean=True)
    def is_past_display(self, obj):
        """Display if past"""
        return obj.is_past

    # NEW: Display meet information with link
    @admin.display(description="Meet")
    def meet_display(self, obj):
        """Display meet information with admin link"""
        if obj.meet:
            meet_admin_url = reverse("admin:meet_meet_change", args=[obj.meet.id])
            return format_html(
                '<a href="{}">{} (Channel: {})</a>',
                meet_admin_url,
                obj.meet.id,
                str(obj.meet.channel_name)[:8] + "...",
            )
        return "-"

    # Custom actions (keep your existing actions)
    @admin.action(description="Mark selected as Confirmed")
    def mark_confirmed(self, request, queryset):
        """Bulk action to confirm appointments"""
        updated = queryset.filter(status=AppointmentStatus.SCHEDULED).update(
            status=AppointmentStatus.CONFIRMED
        )
        self.message_user(request, f"{updated} appointments were marked as confirmed.")

    @admin.action(description="Mark selected as Completed")
    def mark_completed(self, request, queryset):
        """Bulk action to complete appointments"""
        updated = queryset.filter(status=AppointmentStatus.IN_PROGRESS).update(
            status=AppointmentStatus.COMPLETED
        )
        self.message_user(request, f"{updated} appointments were marked as completed.")

    @admin.action(description="Cancel selected appointments")
    def cancel_appointments(self, request, queryset):
        """Bulk action to cancel appointments"""
        updated = queryset.filter(
            status__in=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
        ).update(status=AppointmentStatus.CANCELLED, cancelled_by=CancelledBy.SYSTEM)
        self.message_user(request, f"{updated} appointments were cancelled.")

    actions = [mark_confirmed, mark_completed, cancel_appointments]

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            "patient", "doctor", "patient__user", "doctor__user", "created_by", "meet"
        )

    def save_model(self, request, obj, form, change):
        """Set created_by on save"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
