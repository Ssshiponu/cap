from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.template.loader import render_to_string

import random

def send_otp(email):
    try:
        otp = str(random.randint(100000, 999999))
        send_mail(
            subject='Verification OTP for Chat Autopilot',
            message=f'Veify your email by entering the following OTP',
            html_message=render_to_string(
                'email/otp.html',
                {'otp': otp}
            ),
            from_email= 'Chat Autopilot ' + settings.EMAIL_HOST_USER,
            recipient_list=[email],
        )
        
        return otp
    except Exception as e:
        print(e)
        return None