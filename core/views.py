from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
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

def index(request):
    return render(request, 'core/index.html')

@login_required
def dashboard(request):
    """Main dashboard"""
    user = request.user

    subscription = user.subscription
    
    if request.GET.get('using', '') == 'last-month':
        if subscription.plan == 'free':
            return redirect('/dashboard/?using=last-week')
    
    # Get connected pages
    pages = FacebookPage.objects.filter(user=user)
    
    # Get page stats
    days_ago = lambda days: timezone.now() - timedelta(days=days)
    using_days = request.GET.get('using')
    
    if using_days == 'today':
        day = 1
    elif using_days == 'last-week':
        day = 7
    elif using_days == 'last-month':
        day = 30
    else:
        day = 30
        
        
    colors = list(settings.COLORS.keys())
    using = []
    for index, page in enumerate(pages):
        using.append({
            'name': page.page_name,
            'conversations': Conversation.objects.filter(page_id=page.id, updated_at__gte=days_ago(day)).count(),
            'ai_replies': Message.objects.filter(conversation__page_id=page.id, role='assistant', created_at__gte=days_ago(day)).count(),
            'messages': Message.objects.filter(conversation__page_id=page.id, created_at__gte=days_ago(day)).count(),
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
        'using': using,
        'remaining_using': remaining_using,
        
        'total_ai_replies': total_ai_replies,
        'ai_replies_limit': ai_replies_limit,
        }
    
    return render(request, 'core/dashboard.html', context)


# ============================================
# Facebook Page Management Views
# ============================================

@login_required
def page(request, page_id):
    """View single page details"""
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    plan = request.user.subscription.plan
    
    if request.method == 'POST':
        system_prompt = request.POST.get('system_prompt') 
        business_context = request.POST.get('business_context')
        if system_prompt is not None:
            page.system_prompt = system_prompt.strip()
        
        if business_context is not None:
            page.business_context = business_context.strip()
        
        page.save()    
        return redirect(request.GET.get('next', f'/page/{page_id}'))
    
    # Get page stats
    thirty_days_ago = timezone.now() - timedelta(days=30)
    stats = {
        'total_messages': 0,
        'ai_responses': 0,
        'tottal_conversations': 0,
    }
    
    context = {
        'page': page,
        'stats': stats,
        'max_system_prompt_length': settings.PLANS[plan]['max_system_prompt_length'],
        'max_business_context_length': settings.PLANS[plan]['max_business_context_length'],
    }
    
    return render(request, 'core/page.html', context)


@login_required
@require_POST
def page_toggle(request, page_id):
    """Toggle page enabled status"""
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    page.enabled = not page.enabled
    page.save()    
    return redirect(request.GET.get('next', 'dashboard'))

@login_required
def system_prompt_reset(request, page_id):
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    page.system_prompt = 'You are an helpful ai bot in messenger'
    page.save()
    return redirect(request.GET.get('next', f'/page/{page_id}'))

@login_required
def business_context_reset(request, page_id):
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    page.business_context = 'No business context'
    page.save()    
    return redirect(request.GET.get('next', f'/page/{page_id}'))






@login_required
@require_POST
def page_disconnect(request, page_id):
    """Disconnect a Facebook page"""
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    
    page_name = page.page_name
    page.delete()
    
    messages.success(request, f'{page_name} has been disconnected')
    return redirect('pages_list')


@login_required
def subscription(request):
    """View subscription details"""
    subscription = request.user.subscription
    
    context = {
        'subscription': subscription,
    }
    
    return render(request, 'subscription/detail.html', context)


@login_required
def upgrade_plan(request):
    """Upgrade subscription plan"""
    if request.method == 'POST':
        plan = request.POST.get('plan')
        
        # Update subscription
        subscription = request.user.subscription
        subscription.plan = plan
        subscription.save()
        
        messages.success(request, f'Successfully upgraded to {plan} plan')
        return redirect('subscription')
    
    return render(request, 'subscription/upgrade.html')
