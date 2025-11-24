from django.contrib import admin
from .models import AIModel, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['title', 'version', 'model_type', 'status', 'enabled', 'created_at']
    list_filter = ['model_type', 'status', 'enabled', 'created_at']
    search_fields = ['title', 'description']
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'version', 'model_type', 'status')
        }),
        ('Media & Links', {
            'fields': ('icon_name', 'image', 'model_url', 'docs_url', 'document')
        }),
        ('Tags & Status', {
            'fields': ('tags', 'enabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
