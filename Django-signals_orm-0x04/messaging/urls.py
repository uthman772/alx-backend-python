from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Cached views
    path('conversations/', views.conversation_list, name='conversation_list'),
    path('thread/<int:message_id>/', views.message_thread, name='message_thread'),
    path('unread/', views.unread_messages, name='unread_messages'),
    path('inbox/summary/', views.inbox_summary, name='inbox_summary'),
    
    # Cache management (for testing)
    path('clear-cache/', views.clear_cache, name='clear_cache'),
    path('cache-stats/', views.cache_stats, name='cache_stats'),
    
    # Non-cached views (forms, actions, APIs)
    path('reply/<int:message_id>/', views.create_reply, name='create_reply'),
    path('message/<int:message_id>/mark-read/', views.mark_message_read, name='mark_message_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('api/unread/', views.unread_messages_api, name='unread_messages_api'),
    path('api/thread/<int:message_id>/', views.conversation_thread_api, name='conversation_thread_api'),
    
    # Existing URLs
    path('message/<int:message_id>/', views.message_detail, name='message_detail'),
    path('api/message/<int:message_id>/history/', views.message_history_api, name='message_history_api'),
    path('account/delete/confirmation/', views.delete_account_confirmation, name='delete_account_confirmation'),
    path('account/delete/', views.delete_account, name='delete_account'),
    path('api/user/data/summary/', views.user_data_summary, name='user_data_summary'),
]
