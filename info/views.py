from django.shortcuts import render

# Create your views here.

def privacy(request):
    return render(request, 'info/privacy.html')

def terms(request):
    return render(request, 'info/terms.html')

def refund(request):
    return render(request, 'info/refund.html')

def about(request):
    return render(request, 'info/about.html')

def contact(request):
    return render(request, 'info/contact.html')

def faq(request):
    return render(request, 'info/faq.html')

def help(request):
    return render(request, 'info/help.html', {'article': 'index'})

def help_articles(request, article):
    return render(request, f'info/help.html', {'article': article})



# SEO

def robots(request):
    return render(request, 'info/robots.txt')

def sitemap(request):
    return render(request, 'info/sitemap.xml')