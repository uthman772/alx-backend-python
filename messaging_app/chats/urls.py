
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'conversations', views.ConversationViewSet)
router.register(r'messages', views.MessageViewSet)
router.register(r'my-conversations', views.MyConversationsViewSet, basename='myconversations')

urlpatterns = [
    path('', include(router.urls)),
]