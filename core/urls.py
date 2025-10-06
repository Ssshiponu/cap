from django.urls import path, include
from messenger.views import webhook_view
from .views import *

urlpatterns = [
    path("", index, name="index"),
    path("dashboard/", dashboard, name="dashboard"),
    path("page/<int:page_id>/", page, name="page"),
    path("page-toggle/<int:page_id>/", page_toggle, name="page_toggle"),
    path('system-prompt-reset/<int:page_id>/', system_prompt_reset, name="system_prompt_reset"),
    path("page/<int:page_id>/conversation/<int:conversation_id>/delete/", delete_conversation, name="delete_conversation"),
    path('page/<int:page_id>/delete/', delete_page, name="delete_page"),
    
    # Webhooks
    path('webhook/messenger/', webhook_view),
    
    # Auth
    path('auth/', include('auth.urls')),
    
    
]
