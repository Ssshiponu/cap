from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.core.cache import cache
from django.contrib import messages

import re
import random
from datetime import timedelta

from core.models import Otp
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


def create_otp(user=None, ip=None, otp=None):
    # first inactive all otps
    otp_objs = Otp.objects.filter(user=user)
    for obj in otp_objs:
        obj.otp = None
        obj.save()

    Otp.objects.create(user=user, ip=ip, otp=otp)


def is_rate_limited(ip, limit_name, max_attempts, window_seconds):
    key = f"{limit_name}_{ip}"
    attempts = cache.get(key, 0)
    if attempts >= max_attempts:
        return True
    cache.set(key, attempts + 1, window_seconds)
    return False


def handle_otp_sending(user, ip):
    """Centralized OTP sending logic"""
    # Check daily limit
    if is_rate_limited(ip, 'otp_daily', 3, 86400):
        return (False, 'You have reached the maximum number of OTP requests for today.')

    # Check recent OTP (30-second cooldown)
    if is_rate_limited(ip, 'otp', 1, 30):

        return (False, 'Please wait before requesting another OTP.')

    # Send OTP
    otp_code = send_otp(user)
    if not otp_code:
        return (False, 'Failed to send OTP. Please try again.')

    create_otp(user=user, ip=ip, otp=otp_code)
    return (True, None)