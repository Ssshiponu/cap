from messenger.models import Message, Conversation
from .models import FacebookPage
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate


days_ago = lambda days: timezone.now() - timedelta(days=days)


def credits(start_date=None, end_date=None, pages: list[FacebookPage] = []):
    """Return a json data for chartJS bar graph of credits usage"""
    if start_date is None:
        start_date = days_ago(7)
        
    if end_date is None:
        end_date = timezone.now()
        

    # Make sure start_date <= end_date (swap if provided in reverse)
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Convert to dates for iteration (TruncDate produces date objects)
    start_date_only = start_date.date()
    end_date_only = end_date.date()

    # Build the queryset for messages inside the inclusive range
    queryset = Message.objects.filter(
        created_at__date__gte=start_date_only,
        created_at__date__lte=end_date_only
    )

    if pages:
        page_ids = [p.id for p in pages]
        queryset = queryset.filter(conversation__facebook_page__id__in=page_ids)

    # Group by date and sum credits
    daily_credits_qs = queryset.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total_credits=Sum('credits_used')
    ).order_by('date')

    # Build a mapping date -> total_credits (date is a datetime.date)
    credits_by_date = {
        entry['date']: (entry['total_credits'] or 0)
        for entry in daily_credits_qs
    }

    # Iterate the full inclusive date range to produce labels and data
    labels = []
    data = []
    cur = start_date_only + timedelta(days=1)
    while cur <= end_date_only:
        labels.append(cur.strftime('%b-%d'))
        data.append(credits_by_date.get(cur, 0))
        cur += timedelta(days=1)
        
    return {
        'type': 'bar',
        'data': {
            'labels': labels,
            'datasets': [{
                'label': 'Credits Used',
                'data': data,
                'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            }]
        },
        'options': {
        'responsive': True,
        'scales': { 'y': { 'beginAtZero': True } }
        }
    }

def messages(start_date=None, end_date=None, pages: list[FacebookPage] | None = None):
    """
    Return JSON-ready data for a Chart.js line graph of user messages vs AI replies.
    Produces continuous labels for every day in the inclusive range (start_date .. end_date).
    """
    # sensible defaults
    if start_date is None:
        start_date = days_ago(7)
    if end_date is None:
        end_date = timezone.now()

    # Ensure start_date <= end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Convert to date-only for DB filtering and iteration
    start_date_only = start_date.date()
    end_date_only = end_date.date()

    # Build the queryset for the inclusive date range
    queryset = Message.objects.filter(
        created_at__date__gte=start_date_only,
        created_at__date__lte=end_date_only
    )

    if pages:
        page_ids = [p.id for p in pages]
        queryset = queryset.filter(conversation__facebook_page__id__in=page_ids)

    # Group by date and role, count messages
    daily_stats_qs = queryset.annotate(
        date=TruncDate('created_at')
    ).values('date', 'role').annotate(
        count=Count('mid')
    ).order_by('date')

    # Build mapping: date -> {'user': n, 'assistant': m}
    counts_by_date = {}
    for entry in daily_stats_qs:
        d = entry['date']  # datetime.date
        if d not in counts_by_date:
            counts_by_date[d] = {'user': 0, 'assistant': 0}

        role = (entry.get('role') or '').strip().lower()
        # Accept common role names; default anything else to assistant if it looks like a bot
        if role == 'user':
            counts_by_date[d]['user'] = entry['count']
        elif role == 'assistant' or role in ('bot', 'system', 'ai'):
            counts_by_date[d]['assistant'] = entry['count']
        else:
            # If you have other role names you want to treat explicitly, add them above.
            # For unknown role strings, ignore or aggregate as needed (here we ignore).
            pass

    # Iterate full inclusive date range to produce ordered labels and datasets
    labels = []
    user_data = []
    assistant_data = []

    cur = start_date_only + timedelta(days=1)
    while cur <= end_date_only:
        labels.append(cur.strftime('%b-%d'))
        day_counts = counts_by_date.get(cur, {'user': 0, 'assistant': 0})
        user_data.append(day_counts['user'])
        assistant_data.append(day_counts['assistant'])
        cur += timedelta(days=1)

    # Return Chart.js config-like structure
    return {
        'type': 'line',
        'data': {
            'labels': labels,
            'datasets': [
                {
                    'label': 'User Messages',
                    'data': user_data,
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'tension': 0.1,
                    'fill': True
                },
                {
                    'label': 'AI Replies',
                    'data': assistant_data,
                    'borderColor': 'rgba(153, 102, 255, 1)',
                    'backgroundColor': 'rgba(153, 102, 255, 0.2)',
                    'tension': 0.1,
                    'fill': True
                }
            ]
        },
        'options': {
            'responsive': True,
            'scales': {'y': {'beginAtZero': True}}
        }
    }
