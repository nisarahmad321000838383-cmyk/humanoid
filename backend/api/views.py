from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import StreamingHttpResponse
from django.conf import settings
from django.db.models import Q
import json
import math

from .models import Chat, Message, UserSettings, KnowledgeBase, AccessToken
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ChatSerializer,
    ChatListSerializer,
    MessageSerializer,
    UserSettingsSerializer,
    AdminUserSerializer,
    KnowledgeBaseSerializer,
    AccessTokenSerializer,
)
from .models import UploadedFile
from .serializers import UploadedFileSerializer
from .huggingface_service import HuggingFaceService
from .utils import is_super_admin, assign_access_token_to_user, release_user_access_token

# -----------------------------
# Register
# -----------------------------
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # Explicitly disable authentication

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Assign access token to user (if not admin)
        assign_access_token_to_user(user)
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({
            'user': UserSerializer(user).data,
            'refresh': refresh_token,
            'access': access_token,
        }, status=status.HTTP_201_CREATED)

        # Cookie settings
        secure = not settings.DEBUG
        access_max_age = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
        refresh_max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())

        # Set access token cookie (readable by JS)
        response.set_cookie(
            'access_token',
            access_token,
            max_age=access_max_age,
            secure=secure,
            httponly=False,
            samesite='Lax',
            path='/'
        )

        # Set refresh token cookie (HttpOnly)
        response.set_cookie(
            'refresh_token',
            refresh_token,
            max_age=refresh_max_age,
            secure=secure,
            httponly=True,
            samesite='Lax',
            path='/'
        )

        return response

# -----------------------------
# Login
# -----------------------------
class LoginView(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # Explicitly disable authentication

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        # Find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Authenticate with username (Django's authenticate uses username)
        user = authenticate(username=user.username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Assign access token to user (if not admin)
        assign_access_token_to_user(user)
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({
            'user': UserSerializer(user).data,
            'refresh': refresh_token,
            'access': access_token,
        })

        secure = not settings.DEBUG
        access_max_age = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
        refresh_max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())

        response.set_cookie('access_token', access_token, max_age=access_max_age, secure=secure, httponly=False, samesite='Lax', path='/')
        response.set_cookie('refresh_token', refresh_token, max_age=refresh_max_age, secure=secure, httponly=True, samesite='Lax', path='/')

        return response

# -----------------------------
# Token Refresh (custom to assign access tokens)
# -----------------------------
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

class CustomTokenRefreshView(BaseTokenRefreshView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request, *args, **kwargs):
        # Accept refresh token either from request body or from HttpOnly cookie
        refresh_token = request.data.get('refresh') or request.COOKIES.get('refresh_token')
        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        # Get the user from the refresh token
        refresh_token_obj = RefreshToken(serializer.validated_data['refresh'])
        user_id = refresh_token_obj.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            # Assign access token to user (if not admin)
            assign_access_token_to_user(user)
        except User.DoesNotExist:
            pass
        
        # Build response and set cookies for new tokens (if any)
        resp_data = serializer.validated_data
        response = Response(resp_data, status=status.HTTP_200_OK)

        secure = not settings.DEBUG
        access = resp_data.get('access')
        refresh = resp_data.get('refresh')
        access_max_age = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
        refresh_max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())

        if access:
            response.set_cookie('access_token', access, max_age=access_max_age, secure=secure, httponly=False, samesite='Lax', path='/')
        if refresh:
            response.set_cookie('refresh_token', refresh, max_age=refresh_max_age, secure=secure, httponly=True, samesite='Lax', path='/')

        return response

# -----------------------------
# Logout
# -----------------------------
class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        # Release the user's access token
        release_user_access_token(request.user)
        response = Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        # Delete auth cookies
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        return response

# -----------------------------
# Current authenticated user
# -----------------------------
class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

# -----------------------------
# User settings
# -----------------------------
class UserSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        settings, _ = UserSettings.objects.get_or_create(user=self.request.user)
        return settings
    
    def get_serializer_context(self):
        """Pass request context to serializer for admin checks"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

# -----------------------------
# Chat & Messages
# -----------------------------
class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatListSerializer
        return ChatSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        chat = self.get_object()
        user_message = request.data.get('message', '').strip()
        if not user_message:
            return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Save user message
        user_msg = Message.objects.create(chat=chat, role='user', content=user_message)

        # Prepare conversation
        conversation = [{'role': m.role, 'content': m.content} for m in chat.messages.all()]

        # AI response
        hf_service = HuggingFaceService(user=request.user)
        ai_response = hf_service.generate_response(conversation)

        # Save AI message
        ai_msg = Message.objects.create(chat=chat, role='assistant', content=ai_response)

        # Set chat title if first message
        if chat.messages.count() == 2:
            chat.title = user_message[:50] + ("..." if len(user_message) > 50 else "")
            chat.save()

        return Response({
            'user_message': MessageSerializer(user_msg).data,
            'assistant_message': MessageSerializer(ai_msg).data,
            'chat': ChatSerializer(chat).data
        })

    @action(detail=True, methods=['post'])
    def send_message_stream(self, request, pk=None):
        chat = self.get_object()
        user_message = request.data.get('message', '').strip()
        if not user_message:
            return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        user_msg = Message.objects.create(chat=chat, role='user', content=user_message)
        conversation = [{'role': m.role, 'content': m.content} for m in chat.messages.all()]

        def event_stream():
            hf_service = HuggingFaceService(user=request.user)
            full_response = ""
            yield f"data: {json.dumps({'type': 'start', 'user_message_id': user_msg.id})}\n\n"

            try:
                for chunk in hf_service.generate_response_stream(conversation):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

                cleaned = hf_service.clean_markdown_formatting(full_response)
                yield f"data: {json.dumps({'type': 'replace', 'content': cleaned})}\n\n"

                ai_msg = Message.objects.create(chat=chat, role='assistant', content=cleaned)

                if chat.messages.count() == 2:
                    chat.title = user_message[:50] + ("..." if len(user_message) > 50 else "")
                    chat.save()

                chat.save(update_fields=['updated_at'])
                yield f"data: {json.dumps({'type': 'done', 'assistant_message_id': ai_msg.id, 'chat_id': chat.id})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream', headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        })

    @action(detail=False, methods=['get'])
    def history(self, request):
        chats = self.get_queryset()
        serializer = ChatListSerializer(chats, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def delete_last_assistant_message(self, request, pk=None):
        """Delete the last assistant message from a chat"""
        chat = self.get_object()
        
        # Get the last assistant message
        last_assistant_msg = chat.messages.filter(role='assistant').last()
        
        if not last_assistant_msg:
            return Response({'error': 'No assistant message found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete the message
        message_id = last_assistant_msg.id
        last_assistant_msg.delete()
        
        # Update chat timestamp
        chat.save(update_fields=['updated_at'])
        
        return Response({
            'message': f'Message {message_id} deleted successfully',
            'chat': ChatSerializer(chat).data
        })

    @action(detail=True, methods=['post'])
    def summarize_message(self, request, pk=None):
        """Summarize a specific message to a given number of lines"""
        chat = self.get_object()
        message_id = request.data.get('message_id')
        max_lines = request.data.get('max_lines')
        
        if not message_id:
            return Response({'error': 'message_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not max_lines:
            return Response({'error': 'max_lines is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            max_lines = int(max_lines)
            if max_lines < 1:
                return Response({'error': 'max_lines must be at least 1'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'max_lines must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the message
        try:
            message = chat.messages.get(id=message_id)
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Only allow summarizing assistant messages
        if message.role != 'assistant':
            return Response({'error': 'Only assistant messages can be summarized'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate summary using HuggingFace service
        hf_service = HuggingFaceService(user=request.user)
        summarized_content = hf_service.summarize_text(message.content, max_lines)
        
        # Update the message content
        message.content = summarized_content
        message.save()
        
        # Update chat timestamp
        chat.save(update_fields=['updated_at'])
        
        return Response({
            'message': MessageSerializer(message).data,
            'chat': ChatSerializer(chat).data
        })


# -----------------------------
# Admin Viewsets
# -----------------------------
class IsSuperAdmin(IsAuthenticated):
    """Permission class to check if user is the super admin"""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and is_super_admin(request.user)


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for managing users.
    Only the super admin can edit/delete other accounts (including password and email).
    """


class UploadedFileViewSet(viewsets.ModelViewSet):
    """Allow authenticated users to upload, list and delete their files.

    Validations enforced:
    - User setting `upload_your_files` must be True
    - Each file < 1 MB and allowed extensions
    - Max 10 files per user
    """
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Previously we enforced a per-user setting to allow uploads. Requirement changed:
        # allow uploads for all authenticated users (seeded admin exception removed),
        # but keep validations (size, type, max files).
        _settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)

        # Enforce max files per user
        current_count = UploadedFile.objects.filter(user=request.user).count()
        if current_count >= 10:
            return Response({'error': 'Maximum number of uploaded files reached (10).'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()
    serializer_class = AdminUserSerializer
    permission_classes = [IsSuperAdmin]
    queryset = User.objects.all()
    
    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')


class AdminChatViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for managing chat history of all users.
    Only the super admin can delete chat history of other accounts.
    """
    serializer_class = ChatSerializer
    permission_classes = [IsSuperAdmin]
    queryset = Chat.objects.all()
    
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            return Chat.objects.filter(user_id=user_id).order_by('-updated_at')
        return Chat.objects.all().order_by('-updated_at')
    
    @action(detail=False, methods=['delete'])
    def delete_user_chats(self, request):
        """Delete all chats for a specific user"""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
            count = Chat.objects.filter(user=user).count()
            Chat.objects.filter(user=user).delete()
            return Response({
                'message': f'Successfully deleted {count} chat(s) for user {user.username}'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for managing knowledge base entries.
    Only the super admin can create, update, and delete training data.
    """
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [IsSuperAdmin]
    queryset = KnowledgeBase.objects.all()
    
    def get_queryset(self):
        search = self.request.query_params.get('search', None)
        queryset = KnowledgeBase.objects.all()
        if search:
            queryset = queryset.filter(
                Q(question__icontains=search) | 
                Q(answer__icontains=search)
            )
        return queryset


class AccessTokenViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for managing access tokens.
    Only the super admin can create, update, and delete access tokens.
    """
    serializer_class = AccessTokenSerializer
    permission_classes = [IsSuperAdmin]
    queryset = AccessToken.objects.all()
    
    def get_queryset(self):
        search = self.request.query_params.get('search', None)
        queryset = AccessToken.objects.all()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        return queryset
