import datetime
import requests
from django.utils import timezone
from .models import Message
from django.conf import settings
from core.ai import AI
from core.utils import generate_random_token

def time_ago(dt):
    if not dt:
        return ""
    
    # Ensure timezone-aware comparison
    now = datetime.datetime.now(datetime.timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        
    diff = now - dt
    seconds = diff.total_seconds()

    # Define thresholds
    minute = 60
    hour = 3600
    day = 86400
    week = 604800
    month = 2592000
    year = 31536000

    if seconds < minute:
        return f"{int(seconds)}s ago"
    elif seconds < hour:
        return f"{int(seconds // minute)}m ago"
    elif seconds < day:
        return f"{int(seconds // hour)}h ago"
    elif seconds < week:
        return f"{int(seconds // day)}d ago"
    elif seconds < month:
        return f"{int(seconds // week)}w ago"
    elif seconds < year:
        return f"{int(seconds // month)}mo ago"
    else:
        return f"{int(seconds // year)}y ago"

def generate_str_conversation(conv, ai: "AI"):
    """
    Generate conversation from messages
    """

    messages = conv.messages.order_by("created_at")

    # Find the index of the last item with role history
    history_index = None
    for i, msg in enumerate(messages):
        if msg.role == "history":
            history_index = i
            
    # Take all messages after history index with itself else take last 12
    if history_index is not None:
        qs = messages[history_index:]
    else:
        qs = list(messages)[-12:]
        
    print(len(qs))

    # Generate conversation
    conversation = ""
    for row in qs:
        conversation += (f'[{row.role}: {row.content}]\n')

    # Generate and add history if not found or if conversation has more than 12 messages
    if history_index is None or len(qs) > 12:
        history = ai.generate_history(conversation)
        Message.objects.create(
            mid="rid_" + generate_random_token(),
            conversation=conv,
            role="history",
            content=history,
        )

    # Add last message time to last message of conversation   
    if len(conversation) > 2:
        conversation += f'[LAST MESSAGEED: {time_ago(conv.updated_at)}]'
        
    print(conversation)

    return conversation

def generate_conversation(conv, last_n=30):
    qs = list(conv.messages.order_by("-created_at").values("role", "content", "created_at")[:last_n])[::-1]

    conversation = []
    for row in qs:
        role = row.get("role")
        content = row.get("content", "")

        conversation.append({
            'role': role,
            'content': content,
        })
        
    if len(conversation) > 2: conversation[-1]['last_message'] = time_ago(conv.updated_at) 
    return conversation

def cache_file(url: str) -> str:
    """Cache file from url"""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/142.0.0.0 Safari/537.36",
        "Referer": settings.SITE_URL,
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }
    
    folder = settings.CACHE_DIR
    filename = generate_random_token(length=32)

    r = requests.get(url, headers=headers, timeout=10, stream=True)
    r.raise_for_status()
    filename += r.url.split("/")[-1]
    with open( f"{folder}/{filename}", "wb") as f:
        for chunk in r.iter_content(1024*8):
            if chunk:
                f.write(chunk)
                
    url = f"{settings.SITE_URL}{settings.CACHE_URL}{filename}"
    print(url)
    return url
