from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import AllowAny
from .views import (
    RegisterView,
    LoginView,
    CurrentUserView,
    UserSettingsView,
    CustomTokenRefreshView,
    LogoutView,
    ChatViewSet,
    AdminUserViewSet,
    AdminChatViewSet,
    KnowledgeBaseViewSet,
    AccessTokenViewSet,
    UploadedFileViewSet,
)

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')
router.register(r'admin/chats', AdminChatViewSet, basename='admin-chat')
router.register(r'admin/knowledge-base', KnowledgeBaseViewSet, basename='knowledge-base')
router.register(r'admin/access-tokens', AccessTokenViewSet, basename='access-token')
router.register(r'uploads', UploadedFileViewSet, basename='uploads')

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/user/', CurrentUserView.as_view(), name='current_user'),

    # User settings
    path('settings/', UserSettingsView.as_view(), name='user_settings'),

    # Chat endpoints
    path('', include(router.urls)),
]
