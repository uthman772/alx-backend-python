from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')

# Custom URL patterns for additional actions
custom_urlpatterns = [
    # JWT Authentication endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Current user endpoints
    path('users/me/', views.UserViewSet.as_view({'get': 'me'}), name='user-me'),
]

urlpatterns = [
    # Include router-generated URLs
    path('', include(router.urls)),
    
    # Include custom URL patterns
    path('auth/', include(custom_urlpatterns)),
]

# Add DRF browsable API auth URLs
urlpatterns += [
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]