from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class User(AbstractUser):
    """Extended user model for SaaS platform"""
    id = models.CharField(primary_key=True, editable=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    picture_url = models.URLField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email


class Subscription(models.Model):
    """User subscription plans"""
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('business', 'Business'),
        ('enterprise', 'Enterprise'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('paused', 'Paused'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Billing
      
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'

    def __str__(self):
        return f"{self.user.email} - {self.plan}"


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
        default="You are a helpful customer service assistant."
    )
    business_context = models.TextField(
        blank=True,
        help_text="Information about the business, products, services"
    )
    
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'facebook_pages'


    def __str__(self):
        return f"{self.page_name} ({self.id})"



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
