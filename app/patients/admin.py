from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Patient, PatientKYCRecord, PatientEmergencyContact


class PatientEmergencyContactInline(admin.TabularInline):
    model = PatientEmergencyContact
    extra = 0
    max_num = 2
    fields = [
        "name",
        "relationship",
        "phone_number",
        "email",
        "preferred_contact_method",
    ]
    verbose_name = "Emergency Contact"
    verbose_name_plural = "Emergency Contacts"


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "name",
        "phone_number",
        "gender",
        "dob",
        "city",
        "state",
        "is_active",
        "kyc_status",
    ]
    search_fields = [
        "user__email",
        "name",
        "phone_number",
        "city",
        "state",
        "postal_code",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_filter = ["is_active", "kyc_status", "gender", "dob"]
    ordering = ("-created_at",)
    inlines = [PatientEmergencyContactInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "name",
                    "dob",
                    "phone_number",
                    "gender",
                    "photo",
                    "website",
                    "bio",
                )
            },
        ),
        (
            _("Address Information"),
            {
                "fields": (
                    "address",
                    "city",
                    "state",
                    "country",
                    "postal_code",
                )
            },
        ),
        (
            _("KYC & Status"),
            {
                "fields": (
                    "id_document",
                    "kyc_status",
                    "is_active",
                )
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(PatientKYCRecord)
class PatientKYCRecordAdmin(admin.ModelAdmin):
    list_display = ["patient", "status", "reviewed_by", "reviewed_at"]
    search_fields = [
        "patient__name",
        "patient__user__email",
        "status",
        "reviewed_by__email",
        "reason",
    ]
    readonly_fields = ["reviewed_at"]
    list_filter = [
        "status",
        "reviewed_at",
    ]
    ordering = ("-reviewed_at",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "patient",
                    "status",
                    "reason",
                )
            },
        ),
        (
            _("Review Information"),
            {
                "fields": (
                    "reviewed_by",
                    "reviewed_at",
                )
            },
        ),
    )


@admin.register(PatientEmergencyContact)
class PatientEmergencyContactAdmin(admin.ModelAdmin):
    list_display = [
        "patient",
        "name",
        "relationship",
        "phone_number",
        "email",
        "preferred_contact_method",
    ]
    search_fields = [
        "patient__name",
        "patient__user__email",
        "name",
        "relationship",
        "phone_number",
        "email",
    ]
    list_filter = ["relationship", "preferred_contact_method"]
    ordering = ("patient__name", "name")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "patient",
                    "name",
                    "relationship",
                )
            },
        ),
        (
            _("Contact Information"),
            {
                "fields": (
                    "phone_number",
                    "email",
                    "address",
                    "preferred_contact_method",
                )
            },
        ),
    )
