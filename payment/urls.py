from django.urls import path
from . import views

urlpatterns = [
    path("", views.payment, name="payment"),
    path("checkout/", views.bkash_checkout, name="bkash_checkout"),
    path("execute/", views.bkash_execute, name="bkash_execute"),
    path("webhook/", views.bkash_webhook, name="bkash_webhook"),
]
