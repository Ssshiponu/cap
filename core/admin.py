from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(User)
admin.site.register(FacebookPage)
admin.site.register(Notification)
admin.site.register(WebhookLog)
admin.site.register(CreditTransaction)
admin.site.register(Order)
admin.site.register(Questions)
admin.site.register(WooConnection)
