from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class BkashTransaction(models.Model):
    # A unique reference from your system
    order_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_id = models.CharField(max_length=200, blank=True, null=True)  # returned from bKash “create” or “execute” steps
    status = models.CharField(max_length=50, default="initiated")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    raw_request = models.JSONField(blank=True, null=True)
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.order_id} - {self.status}"
