from django.urls import path, include
from messenger.views import webhook_view
from .views import *

urlpatterns = [
    path("", index, name="index"),
    path("dashboard/", dashboard, name="dashboard"),
    path("apps/", apps, name="apps"),
    path("apps/<str:app_id>/", app, name="app"),
    
    path("messenger/", messenger, name="messenger"),
    path("whatsapp/", whatsapp, name="whatsapp"),
    path("setup-messenger/", setup_messenger, name="setup-messenger"),
    
    # Webhooks
    path('webhook/messenger/<str:app_id>/', webhook_view),
    
    # Auth
    path('auth/', include('auth.urls')),
]
