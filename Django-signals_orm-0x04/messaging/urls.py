from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Threaded conversation URLs
    path('conversations/', views.conversation_list, name='conversation_list'),
    path('thread/<int:message_id>/', views.message_thread, name='message_thread'),
    path('reply/<int:message_id>/', views.create_reply, name='create_reply'),
    path('api/thread/<int:message_id>/', views.conversation_thread_api, name='conversation_thread_api'),
    
    # Existing URLs
    path('message/<int:message_id>/', views.message_detail, name='message_detail'),
    path('api/message/<int:message_id>/history/', views.message_history_api, name='message_history_api'),
    path('account/delete/confirmation/', views.delete_account_confirmation, name='delete_account_confirmation'),
    path('account/delete/', views.delete_account, name='delete_account'),
    path('api/user/data/summary/', views.user_data_summary, name='user_data_summary'),
]
