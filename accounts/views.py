from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django import forms
from .models import Referral, Withdrawal
from services.models import Subscription, Plan
from django.db.models import Sum
import uuid
from django.db import transaction
from django.core.mail import send_mail
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Form for updating the user profile
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']


def generate_referral_code():
    while True:
        code = str(uuid.uuid4()).replace("-", "")[:10]
        if not Referral.objects.filter(referral_code=code).exists():
            return code

@transaction.atomic
def signup(request):
    if request.method == 'POST':
        full_name = request.POST['full_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        referral_code = request.POST.get('referral_code', None)

        first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')

        if password != password2:
            return JsonResponse({'error': 'Passwords do not match.'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists.'}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email is already registered.'}, status=400)

        user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)

        if referral_code:
            try:
                referral_entry = Referral.objects.get(referral_code=referral_code)
                referrer = referral_entry.referred_user

                if not Referral.objects.filter(referred_user=user).exists():
                    Referral.objects.create(referrer=referrer, referred_user=user, referral_code=generate_referral_code())
            except Referral.DoesNotExist:
                return JsonResponse({'error': 'Invalid referral code.'}, status=400)
        else:
            Referral.objects.create(referrer=user, referred_user=user, referral_code=generate_referral_code())

        auth_login(request, user)
        return JsonResponse({'success': 'Account created successfully and logged in.'}, status=200)

    return render(request, 'accounts/login.html')


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return JsonResponse({'success': 'Logged in successfully.'}, status=200)
        else:
            return JsonResponse({'error': 'Invalid username or password.'}, status=400)

    return render(request, 'accounts/login.html')

def logout(request):
    auth_logout(request)
    return redirect('index')

@login_required
def dashboard(request):
    user = request.user
    subscriptions = Subscription.objects.filter(user=user, status='active').order_by('-start_date')

    context = {
        'subscriptions': subscriptions,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def referral(request):
    user = request.user
    referral = Referral.objects.filter(referred_user=user).first()

    if not referral:
        referral = Referral.objects.create(referrer=user, referred_user=user, referral_code=generate_referral_code())

    referred_users = Referral.objects.filter(referrer=user).exclude(referred_user=user)
    total_earnings = referred_users.aggregate(Sum('earnings'))['earnings__sum'] or 0.00

    context = {
        'referral_link': request.build_absolute_uri(f"/accounts/signup/?referral_code={referral.referral_code}"),
        'referred_users': referred_users,
        'total_earnings': total_earnings,
    }
    return render(request, 'accounts/referral.html', context)


@login_required
def withdrawal(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', None)
        payment_method = request.POST.get('payment_method')
        amount = request.POST.get('number')

        try:
            amount = float(amount)
        except ValueError:
            messages.error(request, 'Invalid amount entered. Please enter a valid number.')
            return redirect('referral')

        total_earnings = Referral.objects.filter(referrer=request.user).aggregate(Sum('earnings'))['earnings__sum'] or 0.00

        if amount < 10:
            messages.error(request, 'The minimum amount to withdraw is $10. Please enter a valid amount.')
            return redirect('referral')

        if amount > total_earnings:
            messages.error(request, 'You cannot withdraw more than your total earnings. Please enter a valid amount.')
            return redirect('referral')

        if payment_method == 'paypal':
            paypal_username = request.POST.get('paypal_username')
            new_withdrawal = Withdrawal(
                user=request.user,
                name=name,
                email=email,
                phone=phone,
                payment_method='paypal',
                amount=amount,
                paypal_username=paypal_username,
            )
        elif payment_method == 'crypto':
            crypto_coin = request.POST.get('cryptoCoin')
            crypto_wallet_address = request.POST.get('cryptoWallet')
            new_withdrawal = Withdrawal(
                user=request.user,
                name=name,
                email=email,
                phone=phone,
                payment_method='crypto',
                amount=amount,
                crypto_coin=crypto_coin,
                crypto_wallet_address=crypto_wallet_address,
            )

        new_withdrawal.save()

        email_subject = f'{new_withdrawal.payment_method} withdrawal'
        admin_url = 'https://buzzforless.com/admin/'
        email_body = (
            f'{name}.\n'
            f'There has been a withdrawal request of ${new_withdrawal.amount}. Sign into the admin panel for more info.\n'
            f'Admin Panel: {admin_url}.\n'
        )

        send_mail(
            email_subject,
            email_body,
            'withdrawal@buzzforless.com',
            ['withdrawal@buzzforless.com', 'Okaforambrose2020@gmail.com', 'chinemeremokpara93@gmail.com'],
            fail_silently=False
        )

        messages.success(request, 'Your withdrawal request has been submitted successfully.')
        return redirect('referral')

    return render(request, 'accounts/referral.html')


@login_required
def profile(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=request.user)
        password_form = PasswordChangeForm(user=request.user, data=request.POST)

        if profile_form.is_valid() and password_form.is_valid():
            profile_form.save()
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please fill the form appropriately.')

    else:
        profile_form = UserProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }

    return render(request, 'accounts/profile.html', context)
