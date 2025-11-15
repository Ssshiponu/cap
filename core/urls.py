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
    path("toggle/<int:page_id>/", toggle, name="toggle"),
    path("update_page/<int:page_id>/",  update_page, name="update_page"),
    path('page/<int:page_id>/conversation/<int:conversation_id>/action/', conversation_action, name="conversation_action"),
    path('page/<int:page_id>/delete/', delete_page, name="delete_page"),
    path('page/<int:page_id>/reconnect/', reconnect_page, name="reconnect_page"),
    path('page/<int:page_id>/download-orders/', download_orders, name="download_orders"),
    
    # woo
    path("connect-woo/", connect_woo, name="connect_woo"),
    path("disconnect-woo/", disconnect_woo, name="disconnect_woo"),
    
    # Notification
    path("notification-read/", notification_read, name="notification_read"),

    path("system-prompts/", templates, name="system_prompts"),
    path("buy-credits/", buy_credits, name="buy_credits"),
    # Webhooks
    path('webhook/messenger/', webhook_view),
    
    # Auth
    path('auth/', include('auth.urls')),
    path('payment/', include('payment.urls')),
    
]
