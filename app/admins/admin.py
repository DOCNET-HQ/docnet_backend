from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import AdminProfile


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'name', 'phone_number'
    ]
    search_fields = [
        'user__email', 'user__username', 'name', 'phone_number'
    ]
    readonly_fields = ['id']
    ordering = ('name',)
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'user',
                    'name',
                    'phone_number',
                    'photo',
                )
            }
        ),
        (
            _('System Information'),
            {
                'fields': (
                    'id',
                )
            }
        ),
    )
