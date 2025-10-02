from django.contrib import admin
from .models import Message, Notification

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'subject', 'timestamp', 'is_read']
    list_filter = ['is_read', 'timestamp', 'sender', 'receiver']
    search_fields = ['subject', 'content', 'sender__username', 'receiver__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Message Information', {
            'fields': ('sender', 'receiver', 'subject', 'content')
        }),
        ('Status', {
            'fields': ('is_read', 'timestamp')
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['is_read', 'notification_type', 'created_at']
    search_fields = ['user__username', 'title', 'message_preview']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'message', 'notification_type')
        }),
        ('Content', {
            'fields': ('title', 'message_preview')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
