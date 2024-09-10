from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),  # Corrected spacing
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('referral/', views.referral, name='referral'),
    path('withdrawal/', views.withdrawal, name='withdrawal'),
]
