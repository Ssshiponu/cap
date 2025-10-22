from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, Avg, Sum
from django.db.models.functions import TruncDate
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, datetime
import requests
import hmac
import hashlib
import json
import time

from .models import (
    User, FacebookPage, Notification, CreditTransaction
)

from messenger.models import (
    Message, Conversation
)

from .utils import *
from . import chart
from .chroma import ChromaDB

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    if request.path == '/':
        if 'bn' in lang:
            return redirect('/bn/')
        else:
            return redirect('/en/')
        
    
    context = {
        'packages': settings.PACKAGES[:4]
    }
    return render(request, 'core/index.html', context)

@login_required
def buy_credits(request):
    buy = request.GET.get('buy')
    page = request.user.get_primary_page()
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
        'page': page,
        'packages': settings.PACKAGES
    }
    return render(request, 'core/buy_cradits.html', context=context)

@login_required
def templates(request):
    page = request.user.get_primary_page()
    context = {
        'page': page,
        'templates': settings.SYSTEM_PROMPT_TEMPLATES
    }
    return render(request, 'core/templates.html', context)


@login_required
def dashboard(request):
    page = request.user.get_primary_page()
    if page is not None:
        return redirect(f'/page/{page.id}/overview')
    else:
        return render(request, 'core/welcome.html')

@login_required
def overview(request, page_id):
    """Main """
    page = request.user.get_primary_page(page_id)

    days = 28

    cache_timeout = 60  # 1 minute
    cache_key = f"chart-{page_id}-{days}"

    cached_chart = cache.get(cache_key)
    if cached_chart:
        messages_chart, credits_chart = cached_chart
    else:
        messages_chart = chart.messages(pages=[page], start_date=days_ago(days))
        credits_chart = chart.credits(pages=[page], start_date=days_ago(days))
        cache.set(cache_key, (messages_chart, credits_chart), cache_timeout)

        # Expire the cache in 1 minute
        expiration_time = timezone.now() + timedelta(seconds=cache_timeout)
        cache.set(cache_key + "-expiration", expiration_time, cache_timeout)
    
    
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
        'settings': settings,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def analytics(request, page_id):
    """View single page details with comprehensive statistics"""
    page = request.user.get_primary_page(page_id)

    days = request.GET.get('days', 21)
    days = max(1, min(int(days), 100))

    cache_timeout = 60  # 1 minute
    cache_key = f"chart-{page_id}-{days}"

    cached_chart = cache.get(cache_key)
    if cached_chart:
        messages_chart, credits_chart = cached_chart
    else:
        messages_chart = chart.messages(pages=[page], start_date=days_ago(days))
        credits_chart = chart.credits(pages=[page], start_date=days_ago(days))
        cache.set(cache_key, (messages_chart, credits_chart), cache_timeout)

        # Expire the cache in 1 minute
        expiration_time = timezone.now() + timedelta(seconds=cache_timeout)
        cache.set(cache_key + "-expiration", expiration_time, cache_timeout)
    
    
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
        'settings': settings,
    }
    
    return render(request, 'core/analytics.html', context)

@login_required
def conversations(request, page_id):
    page = request.user.get_primary_page(page_id)
    convs = Conversation.objects.filter(facebook_page=page, active=True)
    
    # ===== PAGINATION =====
    paginator = Paginator(convs.filter(active=True).order_by('-updated_at'), 10)
    page_number = request.GET.get('page', 1)
    context = {
        'page': page,
        'conversations': paginator.get_page(page_number),
    }
    return render(request, 'core/conversations.html', context)

@login_required
def conversation(request, page_id, conversation_id):
    page = request.user.get_primary_page(page_id)
    conversation = get_object_or_404(Conversation, id=conversation_id, facebook_page=page)
    context = {
        'page': page,
        'conversation': conversation,
    }
    return render(request, 'core/conversation.html', context)

@login_required
def page_settings(request, page_id):
    page = request.user.get_primary_page(page_id)
    context = {
        'page': page,
    }
    return render(request, 'core/settings.html', context)



@login_required
def delete_conversation(request, page_id, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, facebook_page__id=page_id, facebook_page__user=request.user)
    conversation.active = False
    conversation.save()
    return redirect(request.GET.get('next', 'dashboard'))

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
    # conversations = Conversation.objects.filter(facebook_page=page)
    # page.delete()
    
    # for c in conversations:
    #     c.active = False
    #     c.save()
    messages.success(request, f'Page {page.page_name} deleted')
    return redirect('dashboard')

@login_required
@require_POST
def reconnect_page(request, page_id):
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    time.sleep(1)
    messages.success(request, f'Page {page.page_name} reconnected')
    
    # TODO: Reconnect logic
    return redirect(request.GET.get('next', 'dashboard'))

@login_required
def notifications_read(request):
    for n in request.user.notifications.filter(read=False):
        n.mark_as_read()
    return JsonResponse({'success': True})

@login_required
@require_POST
def update_page(request, page_id):
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    system_prompt = request.POST.get('system_prompt')
    business_context = request.POST.get('business_context')
    
    if system_prompt:
        if page.system_prompt != system_prompt.strip():
            page.system_prompt = system_prompt.strip()
            messages.success(request, f'System prompt updated')
    if business_context:
        if page.business_context != business_context.strip():
            page.business_context = business_context.strip()
            if ChromaDB(page).add_embeddings(business_context):
                messages.success(request, f'Business context updated')
            else:
                messages.error(request, f'Failed to update business context')
                return redirect(request.GET.get('next', 'dashboard'))
        
    page.save()
    
    return redirect(request.GET.get('next', 'dashboard'))

