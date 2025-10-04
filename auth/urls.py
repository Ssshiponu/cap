from django.urls import path
from . import views

urlpatterns = [
   path('login/', views.login_view, name='login'),
   path('logout/', views.logout_view, name='logout'),
   path('register-lander/', views.register_lander, name='register_lander'),
   path('register/', views.register, name='register'),
   path('password-reset/', views.password_reset, name='password_reset'),
   path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
   path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
   path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
   
   #facebook oauth
   path('fb-callback/', views.fb_callback, name='fb_callback'),
   path('fb-login/', views.fb_login, name='fb_login'),
   
   path('connect-page/', views.connect_page, name="connect_page"),
]