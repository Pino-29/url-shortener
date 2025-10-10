from django.contrib import admin
from .models import URL


@admin.register(URL)
class URLAdmin(admin.ModelAdmin):
    list_display = ['short_code', 'original_url', 'clicks', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['short_code', 'original_url']
    readonly_fields = ['created_at', 'updated_at', 'clicks']
    ordering = ['-created_at']
