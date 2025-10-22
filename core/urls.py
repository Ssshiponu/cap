from django.urls import path, include
from messenger.views import webhook_view
from .views import *

urlpatterns = [
    path("", index, name="index"),
    path("bn/", index, name="index_bn"),
    path("en/", index, name="index_en"),
    
    path("", include('info.urls')),
    
    # Dashboard
    path("dashboard/", dashboard, name="dashboard"),
    path("page/<int:page_id>/overview/", overview, name="overview"),
    path("page/<int:page_id>/analytics/", analytics, name="analytics"),
    path("page/<int:page_id>/conversations/", conversations, name="conversations"),
    path("page/<int:page_id>/conversation/<int:conversation_id>/", conversation, name="conversation"),
    path("page/<int:page_id>/settings/", page_settings, name="settings"),
    
    
    # Page actions
    path("page-toggle/<int:page_id>/", page_toggle, name="page_toggle"),
    path("update_page/<int:page_id>/",  update_page, name="update_page"),
    path("page/<int:page_id>/conversation/<int:conversation_id>/delete/", delete_conversation, name="delete_conversation"),
    path('page/<int:page_id>/delete/', delete_page, name="delete_page"),
    path('page/<int:page_id>/reconnect/', reconnect_page, name="reconnect_page"),
    
    # Notification
    path("notifications-read/", notifications_read, name="notifications_read"),

    path("system-prompts/", templates, name="system_prompts"),
    path("buy-credits/", buy_credits, name="buy_credits"),
    # Webhooks
    path('webhook/messenger/', webhook_view),
    
    # Auth
    path('auth/', include('auth.urls')),
    path('payment/', include('payment.urls')),
    
    
]
