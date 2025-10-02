from django.contrib import admin
from .models import Message, Notification, MessageHistory

class MessageHistoryInline(admin.TabularInline):
    """
    Inline display for message history in the Message admin.
    """
    model = MessageHistory
    extra = 0
    readonly_fields = ['old_subject', 'old_content', 'edited_by', 'edited_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False  # Prevent adding history entries manually

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'subject', 'timestamp', 'is_read', 'edited', 'last_edited']
    list_filter = ['is_read', 'edited', 'timestamp', 'last_edited', 'sender', 'receiver']
    search_fields = ['subject', 'content', 'sender__username', 'receiver__username']
    readonly_fields = ['timestamp', 'last_edited']
    date_hierarchy = 'timestamp'
    
    # Add inline for message history
    inlines = [MessageHistoryInline]
    
    fieldsets = (
        ('Message Information', {
            'fields': ('sender', 'receiver', 'subject', 'content')
        }),
        ('Status', {
            'fields': ('is_read', 'edited', 'timestamp', 'last_edited')
        }),
    )

@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    list_display = ['message', 'old_subject', 'edited_by', 'edited_at']
    list_filter = ['edited_at', 'edited_by']
    search_fields = ['old_subject', 'old_content', 'message__subject', 'edited_by__username']
    readonly_fields = ['message', 'old_subject', 'old_content', 'edited_by', 'edited_at']
    date_hierarchy = 'edited_at'
    
    fieldsets = (
        ('Message Reference', {
            'fields': ('message',)
        }),
        ('Original Content', {
            'fields': ('old_subject', 'old_content')
        }),
        ('Edit Information', {
            'fields': ('edited_by', 'edited_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation of history entries

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
