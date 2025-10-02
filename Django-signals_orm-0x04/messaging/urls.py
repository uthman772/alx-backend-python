from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('message/<int:message_id>/', views.message_detail, name='message_detail'),
    path('api/message/<int:message_id>/history/', views.message_history_api, name='message_history_api'),
]
