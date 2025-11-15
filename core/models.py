from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
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
        if amount > self.credits_left():
            return False

        self.credits_used += amount
        self.save()
        return True

    def add_credits(self, amount, name=None):
        if name != 'Free':
            # TODO: Check if payment system is configured
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
        return self.notifications.all().order_by('read', '-created_at')[:4]

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
            Notification.objects.create(
                user=self, message=message,
                description=description,
                type=type
            )
    
    def get_primary_page(self, page_id=None):
        if page_id is not None:
            page = self.facebook_pages.filter(id=page_id).first()
            if page is not None:
                self.facebook_pages.filter(primary=True, active=True).exclude(id=page_id).update(primary=False)
                page.primary = True
                page.save()
                return page

        primary_page = self.facebook_pages.filter(primary=True, active=True).first()
        if primary_page is not None:
            return primary_page
        return self.facebook_pages.filter(active=True).first()


class CreditTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='credit_transactions'
    )
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
    comment_enabled = models.BooleanField(default=False)
    product_enabled = models.BooleanField(default=False)
    
    primary = models.BooleanField(default=True)
    
    system_prompt = models.TextField(
        help_text="Base instructions for AI behavior",
        default=""
    )
    
    business_context = models.TextField(
        help_text="Extra knowledge about your business or product for ai",
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
    
    
    def get_questions(self):
        return self.questions.filter(is_active=True)
    
    def get_orders_for_date(self, date=timezone.now().today()):
        """Get orders for only a specific date"""
        orders = self.orders.filter(created_at__date=date)
        return orders
    
    
    def get_orders(self, days=7):
        return self.orders.filter(created_at__gte=days_ago(days))
    
    def get_basic_stats(self):
        return {
            'ai_replies': sum(c.messages.filter(role='assistant').count() for c in self.conversations.all()),
            'credits': sum(message.credits_used for message in [m for c in self.conversations.all() for m in c.messages.all()]),
            'fake_conversations': self.conversations.filter(blocked=True).count(),
            'orders': self.orders.count(),
        }
    
    def get_notifications(self):
        return (self.notifications.filter(read=False) | self.user.notifications.filter(read=False)).order_by('-created_at')
    
class WooConnection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facebook_page = models.OneToOneField(FacebookPage, on_delete=models.CASCADE, related_name='woo')
    store_url = models.CharField(max_length=255)
    consumer_key = models.CharField(max_length=255)
    consumer_secret = models.CharField(max_length=255)
    
    connected = models.BooleanField(default=False)
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.store_url
    
    
class Notification(models.Model):
    TYPES = [
        ('success', 'Success'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('helpful', 'Helpful'),
        ('debug', 'Debug'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    FacebookPage = models.ForeignKey(FacebookPage, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    message = models.TextField()
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPES, default='info')
    action_text = models.CharField(max_length=255, blank=True, null=True)
    action_url = models.CharField(max_length=255, blank=True, null=True, default='#')
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
    
    
class Order(models.Model):
    page = models.ForeignKey(FacebookPage, on_delete=models.CASCADE, related_name='orders')
    product = models.CharField(max_length=255)
    suk = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.IntegerField(default=1)
    price = models.IntegerField()
    shipping_cost = models.IntegerField(default=0)
    variation = models.TextField(blank=True, null=True)
    
    customer = models.CharField(max_length=255)
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product} - Q:{self.quantity}"


class Questions(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(FacebookPage, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.question[:50]
    
