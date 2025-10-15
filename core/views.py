from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, Avg, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, datetime
import requests
import hmac
import hashlib
import json

from .models import (
    User, FacebookPage, Notification, CreditTransaction
)

from messenger.models import (
    Message, Conversation
)

from .utils import *
from . import chart

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    context = {
        'packages': settings.PACKAGES[:4]
    }
    return render(request, 'core/index.html', context)

@login_required
def buy_credits(request):
    buy = request.GET.get('buy')
    if buy:
        package = filter(lambda p: p['name'] == buy, settings.PACKAGES)
        package = list(package)
        credits, name = package[0]['credits'], package[0]['name']
        
        added, msg = request.user.add_credits(credits, name=name)
        if not added:
            messages.error(request, msg)
            return redirect(request.GET.get('next', 'buy_credits'))
            
        msg = f'You have {"claimed your free credits" if name == "Free" else f"purchased {credits} credits"}.'
        messages.success(request, msg)
        Notification.objects.create(user=request.user, message=f'{"Free credits" if name == "Free" else "Credits added"} ', description=msg, type='info')
        
        return redirect(request.GET.get('next', 'buy_credits'))
    
    
    context = {
        'packages': settings.PACKAGES
    }
    return render(request, 'core/buy_cradits.html', context=context)

@login_required
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
    """View single page details with comprehensive statistics"""
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    
    # Date ranges
    try:
        days = int(request.GET.get('days', 7))
    except ValueError:
        days = 7

    days = max(1, min(days, 100))
    # Optimized conversation query
    conversations = Conversation.objects.filter(
        facebook_page=page,
        updated_at__gte=days_ago(days)
    ).select_related('facebook_page').prefetch_related('messages')
     
    # Handle POST request for system prompt update
    if request.method == 'POST':
        system_prompt = request.POST.get('system_prompt')
        if system_prompt is not None:
            page.system_prompt = system_prompt.strip()
            page.save()
        return redirect(request.GET.get('next', f'/page/{page_id}'))
    
    
    # ===== PAGINATION =====
    paginator = Paginator(conversations.filter(active=True).order_by('-updated_at'), 10)
    page_number = request.GET.get('page', 1)
    
    messages_chart = chart.messages(pages=[page], start_date=days_ago(days))
    credits_chart = chart.credits(pages=[page], start_date=days_ago(days))
    
    
    # ===== CONTEXT =====
    context = {
        'page': page,

        'charts': {
            'messages': json.dumps(messages_chart),
            'credits': json.dumps(credits_chart),
        },
        'days': days,
        'credits_used': sum(credits_chart.get("data", {}).get("datasets", [{}])[0].get("data", [0])),
        'ai_replies': sum(messages_chart.get("data", {}).get("datasets", [{}])[-1].get("data", [0])),
        'conversations': paginator.get_page(page_number),
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
    page.delete()
    
    for c in conversations:
        c.active = False
        c.save()
    return redirect('dashboard')

@login_required
def notifications_read(request):
    for n in request.user.notifications.filter(read=False):
        n.mark_as_read()
    return JsonResponse({'success': True})