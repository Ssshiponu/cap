from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
import uuid

from .utils import *


class User(AbstractUser):
    """Extended user model for SaaS platform"""
    id = models.CharField(primary_key=True, editable=False)
    ip = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    picture_url = models.URLField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    
    credits = models.IntegerField(default=0)
    credits_used = models.IntegerField(default=0)
    
    

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email
    
    def credits_left(self):
        return self.credits - self.credits_used
    
    def use_credits(self, amount):
        self.credits -= amount
        self.credits_used += amount
        self.save()
        
    def add_credits(self, amount, name=None):
        if name != 'Free':
            return (False, "Payment system is not configured")
        if CreditTransaction.objects.filter(name="Free", ip=self.ip).exists():
            return (False, "Free credits already used")
        
        else:
            CreditTransaction.objects.create(user=self, amount=amount, name=name, ip=self.ip)
            self.credits += amount
            self.save()
            return (True, "Credits added")
        
    def has_credits(self, amount):
        return self.credits_left() >= amount
    
    def is_low_credits(self):
        return self.credits_left() < settings.LOW_CREDIT_THRESHOLD
    
    def has_free_credits(self):
        return not CreditTransaction.objects.filter(name="Free", ip=self.ip).exists()
    
    def notification_list(self):
        return self.notifications.filter(read=False).order_by('-created_at')[:4]
    
            
    def has_notifications(self):
        return self.notifications.filter(read=False).exists()
    
    def get_pages(self):
        return self.facebook_pages.filter(active=True)
    
    def notify(self, message, description=None, type='info'):
        # check same notification already exists in last 24 hours
        if not self.notifications.filter(
            message=message,
            created_at__gte=timezone.now() - timezone.timedelta(days=1)
        ).exists():
            Notification.objects.create(user=self, message=message, description=description, type=type)
    

class CreditTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_transactions')
    ip = models.CharField(max_length=255, blank=True, null=True)
    pages = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class FacebookPage(models.Model):
    """Connected Facebook pages"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
        ('paused', 'Paused'),
    ]

    id = models.IntegerField(primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='facebook_pages')
    active = models.BooleanField(default=True)
    
    # Facebook data
    page_name = models.CharField(max_length=255)
    page_username = models.CharField(max_length=255, blank=True, null=True)
    page_category = models.CharField(max_length=255, blank=True, null=True)
    
    picture = models.TextField(blank=True, null=True)
    
    # OAuth tokens
    access_token = models.TextField()
    token_expires_at = models.DateTimeField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_synced_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Settings
    enabled = models.BooleanField(default=True)
    
    system_prompt = models.TextField(
        help_text="Base instructions for AI behavior",
        default=""
    )
    
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'facebook_pages'


    def __str__(self):
        return f"{self.page_name} ({self.id})"
    
    def credits_per_reply(self):
        return settings.CREDITS_PER_REPLY + round(count_tokens(self.system_prompt) * settings.CREDITS_PER_TOKEN)
    

    
class Notification(models.Model):
    TYPES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPES, default='info')
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        
    def __str__(self):
        return str({'type': self.type, 'message': self.message, 'description': self.description if self.description else ''})
    
    def mark_as_read(self):
        self.read = True
        self.save()




class WebhookLog(models.Model):
    """Log all webhook events from Facebook"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facebook_page = models.ForeignKey(FacebookPage, on_delete=models.CASCADE, related_name='webhook_logs', blank=True, null=True)
    
    type = models.CharField(max_length=100)
    payload = models.JSONField()
    
    error = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'webhook_logs'

    def __str__(self):
        return f"{self.event_type} - {self.created_at}"


class Attempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    attmpt = models.CharField()
    ip = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Otp(models.Model):
    user = models.ForeignKey('core.User', on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    
    def is_expired(self):
        return self.created_at < timezone.now() - timezone.timedelta(minutes=5)
    
    