from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from core.utils import get_ip
from core.limitation import rate_limit

import base64
import requests
import json
import uuid

from core.models import FacebookPage
from .utils import *
from .validator import *

User = get_user_model()


FB_APP_ID = settings.FB_APP_ID
FB_REDIRECT_URI = settings.FB_REDIRECT_URI
FB_APP_SECRET = settings.FB_APP_SECRET

@login_required
def add_page(request):
    """redirect to facebook auth dialogue to add page"""
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
    """callback from facebook auth dialogue to add page"""
    code = request.GET.get("code")
    if not code:
        messages.error(request, "Failed add facebook page")
        return redirect("dashboard")

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
        messages.error(request, "Failed add facebook page")
        return redirect("dashboard")

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


@require_POST
@login_required
def connect_page(request):
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
            if page.user != request.user:
                messages.error(request, f"Page {page_name} already connected to an account")
                continue

            page.active = True
            page.page_name = page_name
            page.page_category = page_category
            page.access_token = page_access_token
            page.picture = picture_data
            page.save()

        else:
            page = FacebookPage.objects.create(
                id=page_id,
                user=request.user,
                page_name=page_name,
                page_category=page_category,
                picture=picture_data,
                access_token=page_access_token,
            )

        try:
            r = subscribe_page(page_id, page_access_token)
        except Exception as e:
            messages.error(request, f"Page {page_name} is connected but cant't reply")
            print(e)
            
        messages.success(request, f"Page {page_name} connected successfully")
            
    return redirect('dashboard')


def login_view(request):
    next = request.GET.get('next') or 'dashboard'
    if request.user.is_authenticated:
        return redirect(next)
    
    if request.method == 'POST':
        email = request.POST['email'].strip().lower()
        password = request.POST['password'].strip()
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
        email = request.POST.get('email', '').strip().lower()
        full_name = request.POST.get('full_name', '').strip()
        password = request.POST.get('password', '')

        # Input validation
        if not all([email, full_name, password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'auth/register.html', {
                'email': email, 
                'full_name': full_name
            })

        # Check for existing active user
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'auth/register.html', {
                'email': email, 
                'full_name': full_name
            })

        # Email validation
        is_valid, message = validate_email(email)
        if not is_valid:
            messages.error(request, message)
            return render(request, 'auth/register.html', {
                'email': email, 
                'full_name': full_name
            })

        # Password validation
        is_valid, message = validate_password(password)
        if not is_valid:
            messages.error(request, message)
            return render(request, 'auth/register.html', {
                'email': email, 
                'full_name': full_name,
                'password': password
            })

        ip = get_ip(request)

        # Get or create inactive user
        user = User.objects.filter(email__iexact=email, is_active=False).first()
        if user:
            # Update existing inactive user
            user.first_name = full_name
            user.set_password(password)
            user.ip = ip
            user.save()
        else:
            # Create new user
            user = User.objects.create_user(
                id=uuid.uuid4(),
                ip=ip,
                first_name=full_name,
                password=password,
                email=email,
                username=generate_random_token(26),
                is_active=False
            )
        
        # Send OTP
        context = {'user_id': user.id, 'resend_seconds': 30, 'type': 'register', 'redirect_url': 'dashboard'}
        is_sent, message = handle_otp_sending(user, ip)
        if not is_sent:
            messages.error(request, message)
            return render(request, 'auth/verify_otp.html', context)
        else:
            return render(request, 'auth/verify_otp.html', context)
    
    # GET request handling
    email = request.GET.get('email', '').strip().lower()
    if not email:
        return redirect('register_lander')
        
    return render(request, 'auth/register.html', {'email': email})


def verify_otp(request):
    if request.method != 'POST':
        return redirect('register_lander')
    
    user_id = request.POST.get('user_id', '')
    otp_code = request.POST.get('otp', '').strip()
    type = request.POST.get('type', '')
    
    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, 'Invalid verification request.')
        return redirect('login')
    
    context = {
            'user_id': user_id, 
            'resend_seconds': 0,
        }
    
    #when otp is valid
    print(cache.get(f"otp_{user.email}"))
    if otp_code == cache.get(f"otp_{user.email}"):
        if type == 'register':
            user.is_active = True
            user.save()
            
            # Delete otp from cache
            cache.delete(f"otp_{user.email}")
            
            # lofin user
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        elif type == 'password_reset':
            # Password reset token for security
            token = generate_random_token()
            cache.set(key=f"reset_password_{user_id}", value=token, timeout=300)
            
            # Delete otp from cache
            cache.delete(f"otp_{user.email}")
            
            return render(request, 'auth/password_reset.html', {'user_id': user_id, 'token': token})
        else:
            messages.error(request, 'Invalid verification request.')
            return redirect('login')
        
    #when otp is invalid
    else:
        messages.error(request, 'Invalid verification code.')
        return render(request, 'auth/verify_otp.html', context)

def password_reset_lander(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if not email:
            messages.error(request, 'Email is required.')
            return render(request, 'auth/password_reset_lander.html', {'email': email})
        
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            messages.error(request, 'No account found with this email.')
            return render(request, 'auth/password_reset_lander.html', {'email': email})
        
        # Send OTP
        ip = get_ip(request)
        context = {'user_id': user.id, 'resend_seconds': 30, 'type': 'password_reset'}
        is_sent, message = handle_otp_sending(user, ip)
        if not is_sent:
            messages.error(request, message)
            context['resend_seconds'] = 0
            return render(request, 'auth/verify_otp.html', context)
        else:
            return render(request, 'auth/verify_otp.html', context)
    
    return render(request, 'auth/password_reset_lander.html')
    

def password_reset(request):
    if request.method != 'POST':
        return redirect('login')
    
    user_id = request.POST.get('user_id', '')
    token = request.POST.get('token', '')
    password = request.POST.get('password', '').strip()
    
    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, 'Invalid verification request.')
        return redirect('login')
    
    if token != cache.get(f"reset_password_{user_id}"):
        messages.error(request, 'Invalid verification request.')
        
    is_valid, message = validate_password(password)
    if not is_valid:
        messages.error(request, message)
        return render(request, 'auth/reset_password.html', {'user_id': user_id, 'token': token, 'password': password})
        
    user.set_password(password)
    user.save()
    cache.delete(f"reset_password_{user_id}")
    logout_from_all(user)
    messages.success(request, 'Password reset successfully!')
    return redirect('login')


    
    