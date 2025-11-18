from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Hospital, HospitalKYCRecord


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "name",
        "phone_number",
        "registration_number",
        "city",
        "state",
        "is_active",
        "is_visible",
        "kyc_status",
        "license_number",
        "license_expiry_date",
    ]
    search_fields = [
        "user__email",
        "name",
        "phone_number",
        "license_number",
        "registration_number",
        "city",
        "state",
        "postal_code",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_filter = [
        "is_active",
        "kyc_status",
        "license_expiry_date",
    ]

    ordering = ("-created_at",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "name",
                    "phone_number",
                    "registration_number",
                    "photo",
                    "cover_image",
                    "website",
                    "bio",
                    "specialties",
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
            _("License Information"),
            {
                "fields": (
                    "license_name",
                    "license_issuance_authority",
                    "license_number",
                    "license_issue_date",
                    "license_expiry_date",
                    "license_document",
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
                    "is_visible",
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


@admin.register(HospitalKYCRecord)
class HospitalKYCRecordAdmin(admin.ModelAdmin):
    list_display = ["hospital", "status", "reviewed_by", "reviewed_at"]
    search_fields = [
        "hospital__name",
        "hospital__user__email",
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
                    "hospital",
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
