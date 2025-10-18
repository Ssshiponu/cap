from django.urls import path
from . import views

urlpatterns = [
   path('login/', views.login_view, name='login'),
   path('logout/', views.logout_view, name='logout'),
   path('register-lander/', views.register_lander, name='register_lander'),
   path('register/', views.register, name='register'),
   path('verify-otp/', views.verify_otp, name='verify_otp'),
   path('password-reset-lander/', views.password_reset_lander, name='password_reset_lander'),
   path('password-reset/', views.password_reset, name='password_reset'),

   #facebook oauth
   path('add-page-callback/', views.add_page_callback, name='add_page_callback'),
   path('add-page/', views.add_page, name='add_page'),
   
   path('connect-page/', views.connect_page, name="connect_page"),
]