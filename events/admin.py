from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Event, EventClient
from django.conf import settings


@admin.register(Event)
class EventAdmin(ModelAdmin):
    list_display = ('title', 'is_active', 'axl_connect', 'axl_pending_webinar_connect', 'luma_connect')
    list_filter = ('is_active', 'axl_connect', 'axl_pending_webinar_connect', 'luma_connect')
    search_fields = ('title', 'luma_event_id', 'axl_webinar_id', 'axl_pending_webinar_id')
    readonly_fields = ('axl_connect', 'axl_pending_webinar_connect', 'luma_connect')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'luma_event_id', 'axl_webinar_id', 'axl_pending_webinar_id', 'is_active')
        }),
        ('Статус подключения', {
            'fields': ('luma_connect', 'axl_connect', 'axl_pending_webinar_connect' ),
            'classes': ('collapse',)
        }),
    )
    

@admin.register(EventClient)
class EventClientAdmin(ModelAdmin):
    list_display = ('name', 'email', 'event', 'approval_status', 'registered_at')
    list_filter = ('approval_status', 'event', 'created_at')
    search_fields = ('name', 'email', 'event__title')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('event', 'name', 'email', 'axl_id', 'approval_status')
        }),
        ('Информация о регистрации', {
            'fields': ('registered_at', 'check_in_qr_code', 'ticket_name')
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        queryset.update(approval_status='approved')
    approve_selected.short_description = 'Подтвердить выбранных участников'
    
    def reject_selected(self, request, queryset):
        queryset.update(approval_status='rejected')
    reject_selected.short_description = 'Отклонить выбранных участников'
