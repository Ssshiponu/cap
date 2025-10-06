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
    User, FacebookPage, Subscription, WebhookLog
)

from messenger.models import (
    Message, Conversation
)

from .utils import *

def index(request):
    
    context = {
        'plans': settings.PLANS
    }
    return render(request, 'core/index.html', context)

@login_required
def dashboard(request):
    """Main dashboard"""
    user = request.user
    subscription = user.subscription
    
    if request.GET.get('using', '') == 'last-month':
        if subscription.plan == 'free':
            return redirect('/dashboard/?using=last-week')
    
    pages = FacebookPage.objects.filter(user=user)
    
    using_days = request.GET.get('using')
    
    if using_days == 'today': day = 1
    elif using_days == 'last-week': day = 7
    elif using_days == 'last-month': day = 30
    else: day = 30
        
        
    colors = list(settings.COLORS.keys())
    using = []
    for index, page in enumerate(pages):
        using.append({
            'name': page.page_name,
            'conversations': Conversation.objects.filter(facebook_page=page, updated_at__gte=days_ago(day)).count(),
            'ai_replies': Message.objects.filter(conversation__facebook_page=page, role='assistant', created_at__gte=days_ago(day)).count(),
            'messages': Message.objects.filter(conversation__facebook_page=page, created_at__gte=days_ago(day)).count(),
            'color': colors[index],
        })
    ai_replies_limit = settings.PLANS[subscription.plan]['max_message']
    
    total_ai_replies = sum([i['ai_replies'] for i in using])
    for i, page in enumerate(using):
        using[i]['percentage'] = round((using[i]['ai_replies'] / ai_replies_limit) * 100, 1)
        
    remaining_using = 100 - sum([i['percentage'] for i in using])

    
    context = {
        'pages': pages,
        'subscription': subscription,
        'using': sorted(using, key=lambda k: k['percentage'], reverse=True),
        'remaining_using': remaining_using,
        
        'total_ai_replies': total_ai_replies,
        'ai_replies_limit': ai_replies_limit,
        }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def page(request, page_id):
    """View single page details"""
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    plan = request.user.subscription.plan
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
        'max_system_prompt_length': settings.PLANS[plan]['max_system_prompt_length'],
        'conversations':  paginator.get_page(page_number),
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
def system_prompt_reset(request, page_id):
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    page.system_prompt = 'You are an helpful ai bot in messenger'
    page.save()
    return redirect(request.GET.get('next', f'/page/{page_id}'))


@login_required
@require_POST
def delete_page(request, page_id):
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    page.active = False
    return redirect('dashboard')