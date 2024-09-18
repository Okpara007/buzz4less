from django.urls import path
from . import views
from django.contrib.auth import views as auth_views  # Import built-in auth views
from .views import CustomPasswordResetView  # Import your custom password reset view

urlpatterns = [
    path('login/', views.login, name='login'),  # Your custom login view
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('referral/', views.referral, name='referral'),
    path('withdrawal/', views.withdrawal, name='withdrawal'),
    path('profile/', views.profile, name='profile'),
    
    # Password reset URL patterns using the custom password reset view
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
