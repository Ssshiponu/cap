from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages

from .utils import validate_username

# Create your views here.

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'auth/login.html', {'error': 'Invalid credentials'})
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
        username = request.POST['username']

        valid, message = validate_username(username)
        if not valid:
            return render(request, 'auth/register.html', {'error': message})
        
        email = request.POST['email']
        full_name = request.POST['full_name']
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email already in use.')
            return render(request, 'auth/register.html', {'email': email, 'full_name': full_name, 'username': username})

        password = request.POST['password']
        
        user = User.objects.create_user(username=username, first_name=full_name, password=password, email=email)
        user.save()
        
        # Auto-login after registration
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        
    if request.method == 'GET':
        email = request.GET.get('email', '')
        if email:
            return render(request, 'auth/register.html', {'email': email})
        return redirect('register_lander')

    return render(request, 'auth/register.html')

def username_exists(request):
    message = ""
    username = request.GET.get('username', None)
    
    exists, message = validate_username(username)

    return JsonResponse({'exists': exists, "message": message})

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
