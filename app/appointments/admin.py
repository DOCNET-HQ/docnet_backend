from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from .models import Appointment
from .choices import AppointmentStatus, CancelledBy


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Appointment model with organized fieldsets
    """
    
    list_display = [
        'id_short',
        'patient_link',
        'doctor_link',
        'appointment_type',
        'status_badge',
        'scheduled_start_time',
        'timezone',
        'is_upcoming_badge',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'appointment_type',
        'timezone',
        'scheduled_start_time',
        'created_at',
        'cancelled_by'
    ]
    
    search_fields = [
        'id',
        'patient__user__first_name',
        'patient__user__last_name',
        'patient__user__email',
        'doctor__user__first_name',
        'doctor__user__last_name',
        'reason',
        'notes'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'duration_display',
        'is_upcoming_display',
        'is_past_display',
        'meeting_link_display'
    ]
    
    date_hierarchy = 'scheduled_start_time'
    
    list_per_page = 25
    
    ordering = ['-scheduled_start_time']
    
    # Organize fields into logical sections using fieldsets
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'id',
                'patient',
                'doctor',
                'created_by'
            ),
            'description': _('Core appointment identification details')
        }),
        (_('Appointment Details'), {
            'fields': (
                'appointment_type',
                'status',
                'reason',
                'notes'
            ),
            'description': _('Information about the appointment type and purpose')
        }),
        (_('Schedule Information'), {
            'fields': (
                'scheduled_start_time',
                'scheduled_end_time',
                'timezone',
                'duration_display',
                'is_upcoming_display',
                'is_past_display'
            ),
            'description': _('Appointment timing and schedule details')
        }),
        (_('Telemedicine Details'), {
            'fields': (
                'meeting_link',
                'meeting_link_display',
                'technical_issues_reported'
            ),
            'classes': ('collapse',),
            'description': _('Video conferencing and technical information')
        }),
        (_('Cancellation Information'), {
            'fields': (
                'cancellation_reason',
                'cancelled_by'
            ),
            'classes': ('collapse',),
            'description': _('Details if appointment was cancelled')
        }),
        (_('Metadata'), {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',),
            'description': _('System timestamps')
        })
    )
    
    # Custom methods for display
    
    @admin.display(description='ID', ordering='id')
    def id_short(self, obj):
        """Display shortened UUID"""
        return str(obj.id)[:8]
    
    @admin.display(description='Patient')
    def patient_link(self, obj):
        """Display patient as clickable link"""
        url = reverse('admin:users_patient_change', args=[obj.patient.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            f"{obj.patient.user.first_name} {obj.patient.user.last_name}"
        )
    
    @admin.display(description='Doctor')
    def doctor_link(self, obj):
        """Display doctor as clickable link"""
        url = reverse('admin:users_doctor_change', args=[obj.doctor.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            f"Dr. {obj.doctor.user.first_name} {obj.doctor.user.last_name}"
        )
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'scheduled': '#ffc107',  # amber
            'confirmed': '#17a2b8',  # cyan
            'in_progress': '#007bff',  # blue
            'completed': '#28a745',  # green
            'cancelled': '#dc3545',  # red
            'no_show': '#6c757d',  # gray
            'rescheduled': '#fd7e14'  # orange
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @admin.display(description='Upcoming', boolean=True)
    def is_upcoming_badge(self, obj):
        """Display if appointment is upcoming"""
        return obj.is_upcoming
    
    @admin.display(description='Duration')
    def duration_display(self, obj):
        """Display appointment duration"""
        if obj.duration:
            return str(obj.duration)
        return '-'
    
    @admin.display(description='Is Upcoming', boolean=True)
    def is_upcoming_display(self, obj):
        """Display if upcoming"""
        return obj.is_upcoming
    
    @admin.display(description='Is Past', boolean=True)
    def is_past_display(self, obj):
        """Display if past"""
        return obj.is_past
    
    @admin.display(description='Meeting Link')
    def meeting_link_display(self, obj):
        """Display meeting link as clickable"""
        if obj.meeting_link:
            return format_html(
                '<a href="{}" target="_blank">Join Meeting</a>',
                obj.meeting_link
            )
        return '-'
    
    # Custom actions
    
    @admin.action(description='Mark selected as Confirmed')
    def mark_confirmed(self, request, queryset):
        """Bulk action to confirm appointments"""
        updated = queryset.filter(
            status=AppointmentStatus.SCHEDULED
        ).update(status=AppointmentStatus.CONFIRMED)
        self.message_user(request, f'{updated} appointments were marked as confirmed.')
    
    @admin.action(description='Mark selected as Completed')
    def mark_completed(self, request, queryset):
        """Bulk action to complete appointments"""
        updated = queryset.filter(
            status=AppointmentStatus.IN_PROGRESS
        ).update(status=AppointmentStatus.COMPLETED)
        self.message_user(request, f'{updated} appointments were marked as completed.')
    
    @admin.action(description='Cancel selected appointments')
    def cancel_appointments(self, request, queryset):
        """Bulk action to cancel appointments"""
        updated = queryset.filter(
            status__in=[
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED
            ]
        ).update(
            status=AppointmentStatus.CANCELLED,
            cancelled_by=CancelledBy.SYSTEM
        )
        self.message_user(request, f'{updated} appointments were cancelled.')
    
    actions = [mark_confirmed, mark_completed, cancel_appointments]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('patient', 'doctor', 'patient__user', 'doctor__user', 'created_by')
    
    def save_model(self, request, obj, form, change):
        """Set created_by on save"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
