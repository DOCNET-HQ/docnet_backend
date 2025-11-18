from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import AdminProfile


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "name",
        "phone_number",
        "country",
    ]
    search_fields = ["user__email", "name", "phone_number"]
    readonly_fields = ["id"]
    ordering = ("name", "country")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "name",
                    "phone_number",
                    "photo",
                )
            },
        ),
        (_("System Information"), {"fields": ("id",)}),
        (
            _("Location Information"),
            {
                "fields": (
                    "country",
                    "state",
                    "city",
                )
            },
        ),
    )
