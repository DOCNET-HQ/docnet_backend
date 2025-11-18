from django.contrib import admin
from .models import DoctorReview, HospitalReview


@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "doctor", "rating", "created_at", "is_updated")
    list_filter = ("rating", "created_at", "updated_at")
    search_fields = ("user__email", "doctor__name", "text")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Basic Information", {"fields": ("user", "doctor", "rating")}),
        ("Review Content", {"fields": ("text",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(HospitalReview)
class HospitalReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "hospital", "rating", "created_at", "is_updated")
    list_filter = ("rating", "created_at", "updated_at")
    search_fields = ("user__email", "hospital__name", "text")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Basic Information", {"fields": ("user", "hospital", "rating")}),
        ("Review Content", {"fields": ("text",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
