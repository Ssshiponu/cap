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
    tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    count = 0
    for token in tokens:
        if len(token) > 6:
            # Long words often split into smaller tokens in LLMs
            count += len(token) // 6 + 1
        else:
            count += 1
    return count
