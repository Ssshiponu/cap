from datetime import datetime, timezone
from .models import Message
from core.ai import AI
from core.utils import generate_random_token

def time_ago(dt):
    if not dt:
        return ""
    
    # Ensure timezone-aware comparison
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
        
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

def generate_conversation(conv, ai: "AI"):
    """
    Generate conversation. 
    first find history index and then take all messages after history index with itself
    if history index is not found, take all messages and generate a history
    """

    messages = conv.messages.order_by("created_at")

    history_index = None
    for i, msg in enumerate(messages):
        if msg.role == "history":
            history_index = i
            
    print(history_index)

    if history_index is not None:
        qs = messages[history_index:]
    else:
        qs = messages[:]

    conversation = []
    for row in qs:
        conversation.append({
            row.role: row.content
            })

    if history_index is None or len(conversation) > 12:
        history = ai.generate_history(conversation)
        print(history)

        Message.objects.create(
            mid="rid_" + generate_random_token(),
            conversation=conv,
            role="history",
            content=history,
        )

    print(conversation)

    if len(conversation) > 2:
        conversation[-1]["last_message"] = time_ago(conv.updated_at)

    return conversation
