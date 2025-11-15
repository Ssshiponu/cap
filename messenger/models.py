from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
        
class Conversation(models.Model):
    facebook_page = models.ForeignKey('core.FacebookPage', on_delete=models.SET_NULL, related_name='conversations', null=True)
    user_id = models.CharField(max_length=100)
    page_id=models.CharField(max_length=100, null=True, blank=True)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    paused = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        
        ordering = ['updated_at']
    
    def __str__(self):
        return f'C: {self.messages.all().first().content[:50]}...'
    
    def total_credits_used(self):
        return sum(message.credits_used for message in self.messages.all())
    
    def last_messaged_at(self):
        last_message = self.messages.all().order_by('-created_at').first()
        if last_message:
            return last_message.created_at
        return timezone.now() + timezone.timedelta(seconds=1)

    
    def can_reply(self):
        if self.blocked:
            return (False, "Conversation is blocked")
        
        if self.messages.count() == 1:
            return (True, "First message")
        
        if self.paused:
            return (False, "Conversation is paused")
        
        last_message = self.messages.filter(role="user").order_by('-created_at').first()
        if last_message.created_at + timezone.timedelta(seconds=5) < timezone.now():
            return (False, "Too Fast")
        
        return (True, "OK")

class Message(models.Model):
    mid = models.CharField(primary_key=True, max_length=100)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True)
    role = models.CharField(max_length=100)
    content = models.JSONField(null=True, blank=True)
    
    credits_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    
    def __str__(self):
        return str(self.content) or "Empty message"
    
    class Meta:
        ordering = ['-created_at']
        
        verbose_name = "Message"
        verbose_name_plural = "Messages"        
        
