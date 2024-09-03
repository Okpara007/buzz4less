from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='services'),
    path('<int:service_id>/', views.service, name='service'),
    path('process_payment/', views.process_payment, name='process_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('cancel-subscription/<int:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook')
]
