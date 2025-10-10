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
    User, FacebookPage, Notification
)

from messenger.models import (
    Message, Conversation
)

from .utils import *

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    context = {
        'packages': settings.PACKAGES[:4]
    }
    return render(request, 'core/index.html', context)

def buy_credits(request):
    if request.GET.get('buy') ==  settings.PACKAGES[0]['name']:
        free_credits = settings.PACKAGES[0]['credits']
        request.user.add_credits(free_credits)
        
        messages.success(request, f'You have been granted {free_credits} free credits')
        Notification.objects.create(user=request.user, message='Free Credits', description=f'You have been granted {free_credits} free credits', type='info')
        
        return redirect(request.GET.get('next', 'dashboard'))
    
    
    context = {
        'packages': settings.PACKAGES
    }
    return render(request, 'core/buy_cradits.html', context=context)

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

def page(request, page_id):
    """View single page details with comprehensive statistics"""
    page = get_object_or_404(FacebookPage, id=page_id, user=request.user)
    
    # Date ranges
    last_30_days = days_ago(30)
    last_7_days = days_ago(7)
    today = days_ago(0)
    
    # Optimized conversation query
    conversations = Conversation.objects.filter(
        facebook_page=page,
        updated_at__gte=last_30_days
    ).select_related('facebook_page').prefetch_related('messages')
    
    # Handle POST request for system prompt update
    if request.method == 'POST':
        system_prompt = request.POST.get('system_prompt')
        if system_prompt is not None:
            page.system_prompt = system_prompt.strip()
            page.save()
        return redirect(request.GET.get('next', f'/page/{page_id}'))
    
    # ===== STATISTICS =====
    
    # Message statistics with optimized aggregation
    message_stats = Message.objects.filter(
        conversation__facebook_page=page,
        created_at__gte=last_30_days
    ).aggregate(
        total_user_messages=Count('mid', filter=Q(role='user')),
        total_ai_replies=Count('mid', filter=Q(role='assistant')),
        total_credits_used=Sum('credits_used'),
        avg_credits_per_message=Avg('credits_used', filter=Q(role='assistant'))
    )
    
    # Conversation statistics
    conversation_stats = conversations.aggregate(
        total_conversations=Count('id'),
        active_conversations=Count('id', filter=Q(active=True)),
        unique_users=Count('user_id', distinct=True),
        total_input_tokens=Sum('input_tokens'),
        total_output_tokens=Sum('output_tokens')
    )
    
    # Recent activity (last 7 days)
    recent_stats = Message.objects.filter(
        conversation__facebook_page=page,
        created_at__gte=last_7_days
    ).aggregate(
        user_messages_7d=Count('mid', filter=Q(role='user')),
        ai_replies_7d=Count('mid', filter=Q(role='assistant')),
        credits_used_7d=Sum('credits_used')
    )
    
    # Today's activity
    today_stats = Message.objects.filter(
        conversation__facebook_page=page,
        created_at__gte=today
    ).aggregate(
        user_messages_today=Count('mid', filter=Q(role='user')),
        ai_replies_today=Count('mid', filter=Q(role='assistant')),
        credits_used_today=Sum('credits_used')
    )
    
    # Response rate calculation
    total_user_msgs = message_stats['total_user_messages'] or 0
    total_ai_msgs = message_stats['total_ai_replies'] or 0
    response_rate = (total_ai_msgs / total_user_msgs * 100) if total_user_msgs > 0 else 0
    
    # Average messages per conversation
    avg_messages_per_conv = (
        (total_user_msgs + total_ai_msgs) / conversation_stats['total_conversations']
        if conversation_stats['total_conversations'] > 0 else 0
    )
    
    # ===== CHART DATA =====
    
    # Daily message activity (last 30 days)
    daily_messages = Message.objects.filter(
        conversation__facebook_page=page,
        created_at__gte=last_30_days
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        user_count=Count('mid', filter=Q(role='user')),
        assistant_count=Count('mid', filter=Q(role='assistant'))
    ).order_by('date')
    
    # Prepare chart data
    date_labels = []
    user_data = []
    assistant_data = []
    
    # Create a dict for easy lookup
    message_dict = {item['date']: item for item in daily_messages}
    
    # Fill in all 30 days (including days with no messages)
    for i in range(30):
        date = (datetime.now() - timedelta(days=29-i)).date()
        date_labels.append(date.strftime('%b %d'))
        
        day_data = message_dict.get(date, {})
        user_data.append(day_data.get('user_count', 0))
        assistant_data.append(day_data.get('assistant_count', 0))
    
    message_chart = {
        'type': 'line',
        'data': {
            'labels': date_labels,
            'datasets': [
                {
                    'label': 'User Messages',
                    'data': user_data,
                    'borderColor': 'rgb(59, 130, 246)',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'tension': 0.4,
                    'fill': True
                },
                {
                    'label': 'AI Replies',
                    'data': assistant_data,
                    'borderColor': 'rgb(16, 185, 129)',
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'tension': 0.4,
                    'fill': True
                }
            ]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': True,
            'aspectRatio': 2,
            'interaction': {
                'mode': 'index',
                'intersect': False
            },
            'plugins': {
                'legend': {
                    'position': 'top',
                },
                'tooltip': {
                    'mode': 'index',
                    'intersect': False
                }
            },
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'ticks': {
                        'precision': 0
                    }
                }
            }
        }
    }
    
    # Credits usage chart (last 30 days)
    daily_credits = Message.objects.filter(
        conversation__facebook_page=page,
        created_at__gte=last_30_days,
        role='assistant'
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        credits=Sum('credits_used')
    ).order_by('date')
    
    credits_dict = {item['date']: item['credits'] for item in daily_credits}
    credits_data = [credits_dict.get((datetime.now() - timedelta(days=29-i)).date(), 0) for i in range(30)]
    
    credits_chart = {
        'type': 'bar',
        'data': {
            'labels': date_labels,
            'datasets': [{
                'label': 'Credits Used',
                'data': credits_data,
                'backgroundColor': 'rgba(139, 92, 246, 0.7)',
                'borderColor': 'rgb(139, 92, 246)',
                'borderWidth': 1
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': True,
            'aspectRatio': 2,
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'ticks': {
                        'precision': 0
                    }
                }
            }
        }
    }
    
    # Top users by message count
    top_users = Message.objects.filter(
        conversation__facebook_page=page,
        created_at__gte=last_30_days,
        role='user'
    ).values('conversation__user_id').annotate(
        message_count=Count('mid')
    ).order_by('-message_count')[:10]
    
    # ===== PAGINATION =====
    paginator = Paginator(conversations.filter(active=True).order_by('-updated_at'), 10)
    page_number = request.GET.get('page', 1)
    
    # ===== CONTEXT =====
    context = {
        'page': page,
        'stats': {
            # 30-day stats
            'user_messages': message_stats['total_user_messages'] or 0,
            'ai_replies': message_stats['total_ai_replies'] or 0,
            'total_conversations': conversation_stats['total_conversations'] or 0,
            'active_conversations': conversation_stats['active_conversations'] or 0,
            'unique_users': conversation_stats['unique_users'] or 0,
            'credits_used': message_stats['total_credits_used'] or 0,
            'avg_credits_per_reply': round(message_stats['avg_credits_per_message'] or 0, 2),
            'response_rate': round(response_rate, 1),
            'avg_messages_per_conv': round(avg_messages_per_conv, 1),
            'total_tokens': (conversation_stats['total_input_tokens'] or 0) + (conversation_stats['total_output_tokens'] or 0),
            
            # 7-day stats
            'user_messages_7d': recent_stats['user_messages_7d'] or 0,
            'ai_replies_7d': recent_stats['ai_replies_7d'] or 0,
            'credits_used_7d': recent_stats['credits_used_7d'] or 0,
            
            # Today's stats
            'user_messages_today': today_stats['user_messages_today'] or 0,
            'ai_replies_today': today_stats['ai_replies_today'] or 0,
            'credits_used_today': today_stats['credits_used_today'] or 0,
        },
        'charts': {
            'messages': json.dumps(message_chart),
            'credits': json.dumps(credits_chart),
        },
        'top_users': top_users,
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
    page.active = False
    page.save()
    
    for c in conversations:
        c.active = False
        c.save()
    return redirect('dashboard')

@login_required
def notifications_read(request):
    for n in request.user.notifications.filter(read=False):
        n.mark_as_read()
    return JsonResponse({'success': True})