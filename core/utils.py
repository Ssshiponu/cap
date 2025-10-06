import random
from datetime import timedelta
from django.utils import timezone

def generate_random_token(length=32):
    """Generate a random webhook verify token."""
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(characters) for _ in range(length))

days_ago = lambda days: timezone.now() - timedelta(days=days)
