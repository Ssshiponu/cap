from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, datetime
import requests
import hmac
import hashlib
import json

from .models import (
    User, FacebookPage
)

from messenger.models import (
    Message, Conversation
)

from .utils import *

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    context = {
        'packages': settings.PACKAGES
    }
    return render(request, 'core/index.html', context)

def templates(request):
    
    context = {
        'templates': settings.SYSTEM_PROMPT_TEMPLATES
    }
    return render(request, 'core/templates.html', context)

@login_required
def dashboard(request):
    """Main dashboard"""
    user = request.user
    pages = FacebookPage.objects.filter(user=user, active=True)
    

    
    context = {
        'pages': pages,
        }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def page(request, page_id):
    """View single page details"""
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    conversations = Conversation.objects.filter(facebook_page=page, updated_at__gte=days_ago(30)).order_by('-updated_at')
    
    user_messages = 0
    ai_replies = 0
    
    paginator = Paginator(conversations.filter(active=True), 10)
    page_number = request.GET.get('page', 1)
    
    for c in conversations:
        user_messages += c.messages.filter(role='user', created_at__gte=days_ago(30)).count()
        ai_replies += c.messages.filter(role='assistant', created_at__gte=days_ago(30)).count()
    
    if request.method == 'POST':
        system_prompt = request.POST.get('system_prompt') 
        if system_prompt is not None:
            page.system_prompt = system_prompt.strip()
        
        page.save()
        return redirect(request.GET.get('next', f'/page/{page_id}'))
    
    # Get page stats
    using = {
        'user_messages': user_messages,
        'ai_replies': ai_replies,
        'conversations': conversations.count(),
        'unique_users': conversations.values('user_id').distinct().count(),
    }
    
    context = {
        'page': page,
        'using': using,
        'conversations':  paginator.get_page(page_number),
        'settings': settings,
    }
    
    return render(request, 'core/page.html', context)

@login_required
def delete_conversation(request, page_id, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, facebook_page__id=page_id, facebook_page__user=request.user)
    conversation.active = False
    conversation.save()
    return redirect(request.GET.get('next', f'/page/{page_id}'))

@login_required
@require_POST
def page_toggle(request, page_id):
    """Toggle page enabled status"""
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    page.enabled = not page.enabled
    page.save()
    status = 'enabled' if page.enabled else 'disabled'
    messages.success(request, f'Page {page.page_name} {status}')
    return redirect(request.GET.get('next', 'dashboard'))

@login_required
@require_POST
def delete_page(request, page_id):
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    conversations = Conversation.objects.filter(facebook_page=page)
    page.active = False
    page.save()
    
    for c in conversations:
        c.active = False
        c.save()
    return redirect('dashboard')