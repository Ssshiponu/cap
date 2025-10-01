from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import App
from .utils import *
# Create your views here.

def index(request):
    return render(request, 'index.html')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def apps(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            token = generate_random_token()
            App.objects.create(user=request.user, name=name, webhook_verify_token=token)
            
        return redirect('apps')
    
    apps = App.objects.filter(user=request.user)
    return render(request, 'apps.html', {'apps': apps})

def app(request, app_id):
    try:
        app = App.objects.get(id=app_id)
        if app.user != request.user:
            return redirect('apps')
    except App.DoesNotExist:
        return redirect('apps')
    
    return render(request, 'app.html', {'app': app})

@login_required
def messenger(request):
    return render(request, 'messenger.html')

@login_required
def whatsapp(request):
    return render(request, 'whatsapp.html')


@login_required
def setup_messenger(request):
    if request.method == 'GET':
        app_id = request.GET.get('app_id')
        if not app_id:
            return redirect('apps')
        
        app = App.objects.get(id=app_id)
        if app.user != request.user:
            return redirect('apps')
        
        
    
        context = {
            'webhook_url': app.get_webhook_url(request),
            'verify_token': app.webhook_verify_token,
            'is_configured': app.is_messenger_configured(),
        }
        return render(request, 'messenger_setup.html', context)
    
    if request.method == 'POST':
        app_id = request.POST.get('app_id')
        page_access_token = request.POST.get('page_access_token')
        app_secret = request.POST.get('app_secret')
        
        app = App.objects.get(id=app_id)
        if app.user != request.user:
            return redirect('apps')
        
        app.fb_access_key = page_access_token
        app.fb_app_secret = app_secret
        app.save()

        return redirect(f'/setup-messenger/?app_id={app.id}#step-4')