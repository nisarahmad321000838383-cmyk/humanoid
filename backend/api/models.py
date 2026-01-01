from django.db import models
from django.contrib.auth.models import User
import json


class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    title = models.CharField(max_length=255, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    theme = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='dark')
    admin_ai_access_token = models.TextField(
        blank=True,
        null=True,
        help_text="Admin-only HuggingFace access token for AI model access"
    )
    # Allow users to enable/disable file uploads in their settings.
    upload_your_files = models.BooleanField(
        default=True,
        help_text='Allow this user to upload files (pdf, docx, pptx, xls, csv).'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Settings"


def _user_upload_path(instance, filename):
    # store uploads under MEDIA_ROOT/user_uploads/<user_id>/<filename>
    return f'user_uploads/{instance.user.id}/{filename}'


class UploadedFile(models.Model):
    """Stores files uploaded by users with simple metadata."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(upload_to=_user_upload_path)
    original_name = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.original_name and self.file:
            self.original_name = getattr(self.file, 'name', '')
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.original_name or (self.file.name if self.file else '')}"


class KnowledgeBase(models.Model):
    """
    Stores training data/knowledge base entries for the chatbot.
    The chatbot will check this database first before using its own knowledge.
    """
    question = models.TextField(help_text="The question or query pattern")
    answer = models.TextField(help_text="The answer to the question")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Knowledge Base Entry'
        verbose_name_plural = 'Knowledge Base Entries'

    def __str__(self):
        return f"Q: {self.question[:50]}..."


class AccessToken(models.Model):
    """
    Stores access tokens that can be managed by admins.
    These tokens can be used for various API integrations or external services.
    Each token can be assigned to one user at a time for HuggingFace API access.
    """
    name = models.CharField(
        max_length=255,
        help_text="A descriptive name for this access token (e.g., 'HuggingFace API', 'OpenAI API')"
    )
    token = models.TextField(
        help_text="The actual access token value"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of what this token is used for"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this token is currently active and usable"
    )
    current_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_access_tokens',
        help_text="The user currently assigned to this token (null if available)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Access Token'
        verbose_name_plural = 'Access Tokens'

    def __str__(self):
        user_info = f" - Assigned to {self.current_user.username}" if self.current_user else " - Available"
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'}){user_info}"
