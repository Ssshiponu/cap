from datetime import datetime, timezone
        

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

        
def get_conversation_json(conv, last_n=20):
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
    print(conversation)
    return conversation

