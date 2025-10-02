from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('message/<int:message_id>/', views.message_detail, name='message_detail'),
    path('api/message/<int:message_id>/history/', views.message_history_api, name='message_history_api'),
    
    # User account deletion URLs
    path('account/delete/confirmation/', views.delete_account_confirmation, name='delete_account_confirmation'),
    path('account/delete/', views.delete_account, name='delete_account'),
    path('api/user/data/summary/', views.user_data_summary, name='user_data_summary'),
]
