from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4

# Create your models here.

    
class App(models.Model):
    id = models.CharField(primary_key=True, default=uuid4(), editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='apps')
    name = models.CharField(max_length=100)
    
    fb_access_key = models.CharField(max_length=255, null=True, blank=True)
    fb_app_secret = models.CharField(max_length=100, null=True, blank=True)
    
    webhook_verify_token = models.CharField(max_length=32)
    
    def __str__(self):
        return f'App: {self.name} ({self.user.username})'
    
    def get_webhook_url(self, request):
        return f'https://{request.get_host()}/webhook/messenger/{self.id}/'

    def is_messenger_configured(self):
        return self.fb_access_key is not None and self.fb_app_secret is not None
