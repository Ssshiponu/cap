import random
import re
from datetime import timedelta
from django.utils import timezone

def generate_random_token(length=32):
    """Generate a random webhook verify token."""
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(characters) for _ in range(length))

days_ago = lambda days: timezone.now() - timedelta(days=days)


def count_tokens(text: str) -> int:
    if not text:
        return 0
    tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    count = 0
    for token in tokens:
        if len(token) > 6:
            # Long words often split into smaller tokens in LLMs
            count += len(token) // 6 + 1
        else:
            count += 1
    return count

def get_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

