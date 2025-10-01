from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

class Config(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='config')
    fb_access_key = models.CharField(max_length=255)
    fb_app_secret = models.CharField(max_length=100)
    webhook_verify_token = models.CharField(max_length=32)
    gemini_api_key = models.CharField(max_length=100)
    
    def __str__(self):
        return f'Config: {self.user.username}'
        
class Conversation(models.Model):
    page_id = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('page_id', 'user_id')
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        
        ordering = ['-updated_at']
    
    def __str__(self):
        return f'C: {self.messages.all().first().content[:50]}... {self.page_id} - {self.user_id}'

class Message(models.Model):
    mid = models.CharField(primary_key=True, max_length=100)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True)
    role = models.CharField(max_length=100)
    content = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    
    def __str__(self):
        return str(self.content) or "Empty message"
    
    class Meta:
        ordering = ['-created_at']
        
        verbose_name = "Message"
        verbose_name_plural = "Messages"

        
        
