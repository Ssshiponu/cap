import time
from django.http import HttpResponse
from django.core.cache import cache

from core.utils import get_ip

def is_rate_limited(ip, limit_name, max_attempts, window_seconds):
    key = f"{limit_name}_{ip}"
    attempts = cache.get(key, 0)
    if attempts >= max_attempts:
        return True
    cache.set(key, attempts + 1, window_seconds)
    return False

#decorator for rate limiting with cache
def rate_limit(limit_name, max_attempts, window_seconds, by_user=False):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if by_user and request.user.is_authenticated:
                identifier = f"user_{request.user.id}"
            else:
                identifier = get_ip(request)
            
            if is_rate_limited(identifier, limit_name, max_attempts, window_seconds):
                return HttpResponse("Too many requests.", status=429)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
