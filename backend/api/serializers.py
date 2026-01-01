from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Chat, Message, UserSettings, KnowledgeBase, AccessToken, UploadedFile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label='Confirm Password')

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        # Create default settings for the user
        UserSettings.objects.create(user=user)
        return user


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'role', 'content', 'created_at')


class ChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ('id', 'title', 'created_at', 'updated_at', 'messages', 'message_count')
        read_only_fields = ('created_at', 'updated_at')

    def get_message_count(self, obj):
        return obj.messages.count()


class ChatListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ('id', 'title', 'created_at', 'updated_at', 'message_count', 'last_message')

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'content': last_msg.content[:50],
                'role': last_msg.role
            }
        return None


class UserSettingsSerializer(serializers.ModelSerializer):
    admin_ai_access_token = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Admin-only HuggingFace access token for AI model access"
    )
    upload_your_files = serializers.BooleanField(required=False, help_text='Allow uploading files (pdf, docx, pptx, xls, csv)')
    
    class Meta:
        model = UserSettings
        fields = ('theme', 'admin_ai_access_token', 'upload_your_files', 'updated_at')
    
    def to_representation(self, instance):
        """Only show admin_ai_access_token to admin users"""
        ret = super().to_representation(instance)
        request = self.context.get('request')
        
        # Check if user is admin
        if request and hasattr(request, 'user'):
            from .utils import is_super_admin
            if is_super_admin(request.user):
                # For admins, show the actual token value so they can edit it
                ret['admin_ai_access_token'] = instance.admin_ai_access_token or ''
            else:
                # For non-admins, don't show this field
                ret.pop('admin_ai_access_token', None)
        else:
            # No request context, don't show
            ret.pop('admin_ai_access_token', None)
        
        return ret
    
    def validate(self, attrs):
        """Only allow admins to set admin_ai_access_token"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            from .utils import is_super_admin
            if 'admin_ai_access_token' in attrs and not is_super_admin(request.user):
                raise serializers.ValidationError({
                    'admin_ai_access_token': 'Only admins can set this field.'
                })
        return attrs


class UploadedFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = UploadedFile
        fields = ('id', 'file', 'original_name', 'created_at')
        read_only_fields = ('original_name', 'created_at')

    def validate_file(self, value):
        """Validate file extension and size (max 1MB)."""
        # Size check
        max_bytes = 1 * 1024 * 1024  # 1 MB
        if value.size > max_bytes:
            raise serializers.ValidationError('Each file must be less than 1 MB.')

        # Extension check
        allowed_exts = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.csv']
        name = value.name.lower()
        if not any(name.endswith(ext) for ext in allowed_exts):
            raise serializers.ValidationError('Invalid file type. Allowed: pdf, doc, docx, ppt, pptx, xls, xlsx, csv')

        return value

    def create(self, validated_data):
        request = self.context.get('request')
        user = None
        if request and hasattr(request, 'user'):
            user = request.user
        uploaded_file = UploadedFile.objects.create(user=user, file=validated_data['file'])
        return uploaded_file


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin to manage users (including password and email)"""
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'date_joined', 'is_active')
        read_only_fields = ('date_joined',)
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBase
        fields = ('id', 'question', 'answer', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class AccessTokenSerializer(serializers.ModelSerializer):
    current_user_username = serializers.SerializerMethodField()
    
    class Meta:
        model = AccessToken
        fields = ('id', 'name', 'token', 'description', 'is_active', 'current_user', 'current_user_username', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at', 'current_user_username')
    
    def get_current_user_username(self, obj):
        return obj.current_user.username if obj.current_user else None
