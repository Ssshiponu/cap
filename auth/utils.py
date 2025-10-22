from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.core.cache import cache
from django.contrib import messages

import re
import random
from datetime import timedelta

from core.limitation import is_rate_limited
from .mail import send_otp


def generate_random_token(length=32):
    """Generate a random string token."""
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(characters) for _ in range(length))


def logout_from_all(user):
    """Logout user from all sessions."""
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.id):
            session.delete()


def handle_otp_sending(user, ip):
    """Centralized OTP sending logic"""
    # Check daily limit
    if is_rate_limited(ip, 'otp_daily', 5, 86400):
        return (False, 'You have reached the maximum number of OTP requests for today.')

    # Check recent OTP (30-second cooldown)
    if is_rate_limited(ip, 'otp', 1, 30):

        return (False, 'Please wait before requesting another OTP.')

    # Send OTP
    otp_code = send_otp(user)
    if not otp_code:
        return (False, 'Failed to send OTP. Please try again.')

    cache.set(f"otp_{user.email}", otp_code, 300)
    return (True, None)