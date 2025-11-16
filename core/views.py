from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, Avg, Sum
from django.db.models.functions import TruncDate
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, datetime
from urllib.parse import unquote
from woocommerce import API
import requests
import hmac
import hashlib
import json
import time
import csv
import os

from .models import (
    User, FacebookPage, Notification, CreditTransaction, WooConnection, Order
)

from messenger.models import (
    Message, Conversation
)

from .utils import *
from . import chart
# from .chroma import ChromaDB

def index(request):
    
    lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    
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
    user = request.user
    
    if user.has_free_credits():
        added, _ = user.add_credits(1000, name='Free')
        if added:
            user.notify(
                message = "You got 1000 free credits. (10 credits per reply)",
                type='info',
            )
    
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
    
    order_days = request.GET.get('days')
    orders = page.get_orders(days=int(order_days) if order_days else 7)

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
        'orders': orders,
        'order_days': order_days,
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
        'basic': page.get_basic_stats(),
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
        'settings': settings,
    }
    return render(request, 'core/settings.html', context)



@login_required
def conversation_action(request, page_id, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, facebook_page__id=page_id, facebook_page__user=request.user)
    action = request.GET.get('action')
    if action == 'pause':
        conversation.paused = True
        conversation.save()
    elif action == 'resume':
        conversation.paused = False
        conversation.save()
    elif action == 'delete':
        conversation.active = False
        conversation.save()
    
    return redirect(request.GET.get('next', 'dashboard'))

@login_required
@require_POST
def toggle(request, page_id):
    """Toggle page enabled status"""
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    t = request.GET.get('t')
    if t == 'replies':
        page.enabled = not page.enabled
        page.save()
        status = 'enabled' if page.enabled else 'disabled'
        message = f'Page {page.page_name} replies {status}'
    elif t == 'comments':
        page.comment_enabled = not page.comment_enabled
        page.save()
        status = 'enabled' if page.comment_enabled else 'disabled'
        message = f'Page {page.page_name} comments {status}'
        
    elif t == 'product':
        page.product_enabled = not page.product_enabled
        page.save()
        status = 'enabled' if page.product_enabled else 'disabled'
        message = f'Page {page.page_name} products {status}'
        
    else:
        return JsonResponse({'success': False, 'type': 'error', 'message': 'Invalid request', 'status': 400})
        
    
    return JsonResponse({'success': True, 'type': 'success', 'message': message, 'status': 200})

@login_required
@require_POST
def delete_page(request, page_id):
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    conversations = Conversation.objects.filter(facebook_page=page)
    page.delete()
    
    for c in conversations:
        c.active = False
        c.save()
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
def notification_read(request):
    id = request.GET.get('id')
    Notification.objects.filter(id=id).update(read=True)
    return JsonResponse({'success': True})

@login_required
def download_orders(request, page_id):
    """Download orders as CSV"""
    # Get the model dynamically
    days = request.GET.get('days')
    days = int(days) if days else 7
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    queryset = page.get_orders()

    if not queryset.exists():
        messages.error(request, "No data found in the table.")
        return redirect(request.GET.get('next', 'dashboard'))

    # Get field names (excluding relations)
    field_names = [field.name for field in Order._meta.get_fields() if not field.is_relation]
    file = os.path.join(settings.CACHE_DIR, f'orders-{generate_random_token(8)}.csv')
    print(file)
    # Write to CSV
    with open(file, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(field_names)  # header row

        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)
            
    return FileResponse(open(file, 'rb'), as_attachment=True)



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
            if True:#ChromaDB(page).add_embeddings(business_context):
                messages.success(request, f'Business context updated')
            else:
                messages.error(request, f'Failed to update business context')
                return redirect(request.GET.get('next', 'dashboard'))
        
    page.save()
    
    return redirect(request.GET.get('next', 'dashboard'))



@login_required
@require_POST
def connect_woo(request):
    data = request.POST
    page_id = data.get('page_id')
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    
    store_url = data.get('store_url').strip()
    consumer_key = data.get('consumer_key').strip()
    consumer_secret = data.get('consumer_secret').strip()
    
    if page and store_url and consumer_key and consumer_secret:
        
        try:
            WooConnection.objects.filter(facebook_page=page).delete()
            woo = WooConnection.objects.create(
                facebook_page=page,
                store_url=store_url,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
            )
        
            # test connection
            wcapi = API(
                url=store_url,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                version="wc/v3",
                timeout=10,
                user_agent="chatautopilot"
            )
            r = wcapi.get("products", params={"per_page": 1})
            
            if r.status_code == 200:
                # try requesting as facebook bot
                r = requests.get(
                    store_url,
                    headers={
                        "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
                    }
                )
                if r.status_code == 200:
                    woo.connected = True
                    woo.save()
                    messages.success(request, f'WooCommerce connection established')
                
                else:
                    woo.error = "Your site blocking requests from facebook. make sure 'facebookexternalhits' is allowed in robots.txt"
                    woo.save()
                    messages.error(request, "Your site blocking requests from facebook.")
            
            else:
                error=f"Your site blocking us. Please make sure all fields are correct and '{wcapi.user_agent}' is allowed in robots.txt"
                woo.error = r.text
                woo.save()
                messages.error(request, "Your site blocking us.")
        except Exception as e:
            print(e)
            error = "Unknown error, please try again with valid credentials"
            woo.error = error
            woo.save()
            messages.error(request, error)
            
            
    else:
        messages.error(request, "All fields are required")
        
    return redirect("settings", page_id = page_id)
            

@login_required
def disconnect_woo(request):
    page_id = request.GET.get('page_id')
    woo = get_object_or_404(WooConnection, facebook_page__id=page_id, facebook_page__user=request.user)
    woo.delete()
    messages.success(request, f'WooCommerce connection removed')
    return redirect("settings", page_id = page_id)
            
            
        
    