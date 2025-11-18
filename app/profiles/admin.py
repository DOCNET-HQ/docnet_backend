from .models import Specialty
from django.contrib import admin


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "description",
    ]
    search_fields = [
        "id",
        "name",
    ]
    readonly_fields = [
        "id",
    ]
    list_filter = [
        "name",
    ]
    ordering = ("-name",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "name",
                    "description",
                    "image",
                )
            },
        ),
    )
