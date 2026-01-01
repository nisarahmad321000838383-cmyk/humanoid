from django.contrib import admin
from .models import Chat, Message, UserSettings, KnowledgeBase, AccessToken


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'user__username')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'role', 'content_preview', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content',)

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = 'Content'


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'updated_at')
    list_filter = ('theme',)


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_preview', 'answer_preview', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('question', 'answer')
    
    def question_preview(self, obj):
        return obj.question[:100] + ("..." if len(obj.question) > 100 else "")
    question_preview.short_description = 'Question'
    
    def answer_preview(self, obj):
        return obj.answer[:100] + ("..." if len(obj.answer) > 100 else "")
    answer_preview.short_description = 'Answer'


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'token_preview', 'is_active', 'current_user', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'current_user__username', 'current_user__email')
    
    def token_preview(self, obj):
        if len(obj.token) > 30:
            return obj.token[:30] + "..."
        return obj.token
    token_preview.short_description = 'Token'
