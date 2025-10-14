from django.urls import path

from . import views

urlpatterns = [
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("refund/", views.refund, name="refund"),
    
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    
    path("products/", views.products, name="products"),
    
    path("help/", views.help, name="help"),
    path("help/<str:article>", views.help_articles, name="help_articles"),
    
    path("faq/", views.faq, name="faq"),    
    
    
    # SEO
    
    path("robots.txt", views.robots, name="robots"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
]