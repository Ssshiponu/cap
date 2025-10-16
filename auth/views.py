from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from core.utils import get_ip

import base64
import requests
import json
import uuid
import random
from datetime import timedelta

from core.models import User, FacebookPage, Attempt, Otp
from .utils import generate_random_token


FB_APP_ID = settings.FB_APP_ID
FB_REDIRECT_URI = settings.FB_REDIRECT_URI
FB_APP_SECRET = settings.FB_APP_SECRET



def add_page(request):
    scope = ",".join([
        "public_profile",
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_metadata",
        "pages_messaging",
    ])
    auth_url = (
        f"https://www.facebook.com/v17.0/dialog/oauth"
        f"?client_id={FB_APP_ID}"
        f"&redirect_uri={FB_REDIRECT_URI}"
        f"&scope={scope}"
        f"&response_type=code"
    )
    return redirect(auth_url)

def add_page_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("No code provided", status=400)

    # Exchange code -> user access token
    token_url = "https://graph.facebook.com/v17.0/oauth/access_token"
    params = {
        "client_id": FB_APP_ID,
        "redirect_uri": FB_REDIRECT_URI,
        "client_secret": FB_APP_SECRET,
        "code": code,
    }
    resp = requests.get(token_url, params=params)
    data = resp.json()

    user_access_token = data.get("access_token")
    if not user_access_token:
        return HttpResponse("Failed to get access token: " + json.dumps(data), status=400)
    
    
    # me_url = "https://graph.facebook.com/v17.0/me"
    # r = requests.get(me_url, params={"access_token": user_access_token, "fields": "id,name,email"})
    # me = r.json()

    # Get pages the user manages (me/accounts)
    pages_url = "https://graph.facebook.com/v17.0/me/accounts"
    r = requests.get(pages_url, params={"access_token": user_access_token})
    pages = r.json().get("data", [])
    
    for page in pages:
        page_id = page.get("id")
        resp = requests.get(f"https://graph.facebook.com/v17.0/{page_id}/picture/?type=small")
        picture_data = base64.b64encode(resp.content).decode("utf-8")
        page["picture"] = f'data:image/png;base64,{picture_data}'
    
    return render(request, 'auth/connect_page.html', {"pages": pages})
            
def connect_page(request):
    if request.method == 'POST':
        pages = request.POST['pages']
        pages = json.loads(pages)
        for page in pages:
            page_id = page.get("id")
            page_name = page.get("name")
            page_access_token = page.get("access_token")
            page_category = page.get("category", "No category")
            picture_data = page.get("picture")

            
            page = FacebookPage.objects.filter(id=page_id).first()
            
            
            
            if page is not None:
                page.active = True
                page.user = request.user
                page.page_name = page_name
                page.page_category = page_category
                page.access_token = page_access_token
                page.picture = picture_data
                page.save()
                continue
            
            FacebookPage.objects.create(
                id = page_id,
                user=request.user,
                page_name=page_name,
                page_category=page_category,
                picture=picture_data,
                access_token=page_access_token,
            )
            
            subscribe_url = f"https://graph.facebook.com/v17.0/{page_id}/subscribed_apps"
            r = requests.post(
                subscribe_url,
                params={"access_token": page_access_token},
                json={"subscribed_fields": ["messages", "messaging_postbacks"]}
            )
            
        return redirect('dashboard')
    return HttpResponse("Method not allowed")


def login_view(request):
    next = request.GET.get('next') or 'dashboard'
    if request.user.is_authenticated:
        return redirect(next)
    
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            
            login(request, user)
            return redirect(next)
        else:
            messages.error(request, "Invalid email or pasword")
            return render(request, 'auth/login.html', {"email": email})
    return render(request, 'auth/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

def register_lander(request):
    return render(request, 'auth/register_lander.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        
        email = request.POST['email']
        full_name = request.POST['full_name']
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            messages.error(request, 'Email already in use.')
            return render(request, 'auth/register.html', {'email': email, 'full_name': full_name})

        user = User.objects.filter(email__iexact=email, is_active=False).first()
            
        password = request.POST['password']
        ip = get_ip(request)
        if user is None:
            user = User.objects.create_user(id=uuid.uuid4(), ip=ip, first_name=full_name, password=password, email=email, username=generate_random_token(26), is_active=False)
        
        # Send Otp if not already 1 sent in last 30 seconds and 3 sent in 1 day
        otp_objs = Otp.objects.filter(user=user, created_at__gte=timezone.now() - timedelta(days=1))
        print(otp_objs.count())
        if otp_objs.count() < 3:
            otp = str(random.randint(100000, 999999))
            print('sending otp..')
                
            try:
                send_mail(
                    subject='Verification OTP for Chat Autopilot',
                    message=f'Veify your email by entering the following OTP',
                    html_message=render_to_string(
                        'email/otp.html',
                        {'otp': otp}
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                )

                Otp.objects.create(user=user, ip=ip, otp=otp)
                
            except Exception as e:
                print(e)
                messages.error('Email could not be sent. Please try again')
                return render(request, 'auth/verify_otp.html', {'user_id': user.id})
        
        else:
            messages.error(request, 'You have already sent 3 OTPs. Please try again 24 hours later.')
            return render(request, 'auth/verify_otp.html', {'user_id': user.id, 'resend_seconds': 0})
        
        return render(request, 'auth/verify_otp.html', {'user_id': user.id, 'resend_seconds': otp_objs.first().get_resend_seconds()})
                
        
    if request.method == 'GET':
        email = request.GET.get('email', '')
        if email:
            if User.objects.filter(email__iexact=email, is_active=True).exists():
                messages.error(request, 'Email already in use.')
            return render(request, 'auth/register.html', {'email': email})
        return redirect('register_lander')

    return render(request, 'auth/register.html')


def verify_otp(request):
    if request.method == 'POST':
        user_id = request.POST['user_id']
        user = User.objects.filter(id=user_id).first()
        if user is None:
            messages.error(request, 'Invalid user')
            return render(request, 'auth/verify_otp.html')
        
        otp = request.POST['otp']
        otp_obj = Otp.objects.filter(user=user, otp=otp).first()
        if otp_obj is None:
            messages.error(request, 'Invalid OTP')
            return render(
                request,
                'auth/verify_otp.html',
                {'user_id': user_id, 'resend_seconds': Otp.objects.filter(user=user).first().get_resend_seconds()}
            )
        
        elif otp_obj.created_ago() > 300:
            messages.error(request, 'OTP has expired')
            return render(request, 'auth/verify_otp.html', {'user_id': user_id})
        else:
            user.is_active = True
            user.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect('dashboard')
    
    return redirect('register_lander')

def password_reset(request):
    if request.method == 'POST':
        email = request.POST['email']
        # Handle password reset logic here
        return render(request, 'auth/password_reset_done.html')
    return render(request, 'auth/password_reset.html')

def password_reset_done(request):
    return render(request, 'auth/password_reset_done.html')

def password_reset_confirm(request, uidb64, token):
    return render(request, 'auth/password_reset_confirm.html')

def password_reset_complete(request):
    return render(request, 'auth/password_reset_complete.html')
