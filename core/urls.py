from django.urls import path
from messenger.views import webhook_view

urlpatterns = [
    path('<str:username>/webhook/m', webhook_view),
]
