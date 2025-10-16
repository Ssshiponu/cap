from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone

import re
import random

from core.models import Otp

def generate_random_token(length=32):
    """Generate a random webhook verify token."""
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
    
