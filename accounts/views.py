from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .models import Referral, Profile, Withdrawal
from services.models import Subscription, Plan
from django.db.models import Sum
import uuid
from django.db import transaction
from django.core.mail import send_mail
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Function to generate a unique referral code
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

        # Split full name into first name and last name
        first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')

        # Validate the form data
        if password != password2:
            return JsonResponse({'error': 'Passwords do not match.'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists.'}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email is already registered.'}, status=400)

        # Create user with inactive status (awaiting email verification)
        user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        user.is_active = False  # Deactivate user until email verification
        user.save()

        # Create a Profile for email verification
        profile = Profile.objects.create(user=user)
        profile.generate_verification_code()  # Generate a verification code

        # Send verification email
        send_mail(
            'Email Verification',
            f'Your verification code is {profile.verification_code}. The code expires in 10 minutes.',
            ['chinemeremokpara93@gmail.com', 'Okaforambrose2020@gmail.com'],  # Replace with your sender email
            [email],
            fail_silently=False,
        )

        # Referral logic (unchanged)
        if referral_code:
            try:
                referral_entry = Referral.objects.get(referral_code=referral_code)
                referrer = referral_entry.referred_user

                if not Referral.objects.filter(referred_user=user).exists():
                    Referral.objects.create(referrer=referrer, referred_user=user, referral_code=str(uuid.uuid4())[:10])
            except Referral.DoesNotExist:
                return JsonResponse({'error': 'Invalid referral code.'}, status=400)
        else:
            Referral.objects.create(referrer=user, referred_user=user, referral_code=str(uuid.uuid4())[:10])

        return JsonResponse({'success': 'Account created. Please check your email for the verification code.'}, status=200)

    return render(request, 'accounts/login.html')

# View to handle email verification
def verify_email(request):
    if request.method == 'POST':
        email = request.POST['email']
        verification_code = request.POST['verification_code']

        try:
            user = User.objects.get(email=email)
            profile = Profile.objects.get(user=user)

            # Check if the verification code matches and hasn't expired
            if profile.verification_code == verification_code and timezone.now() < profile.verification_code_expires_at:
                profile.is_verified = True
                user.is_active = True  # Activate the user
                profile.save()
                user.save()
                return JsonResponse({'success': 'Email verified successfully. You can now log in.'}, status=200)
            else:
                return JsonResponse({'error': 'Invalid or expired verification code.'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'error': 'No account found with this email.'}, status=400)

    return render(request, 'accounts/verify_email.html')

# Modified login view with email verification check
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if the user's email is verified before logging in
            profile = Profile.objects.get(user=user)
            if not profile.is_verified:
                return JsonResponse({'error': 'Please verify your email before logging in.'}, status=400)

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
        admin_url = 'https://127.0.0.1:8000/admin/'
        email_body = (
            f'{name}.\n'
            f'There has been a withdrawal request of ${new_withdrawal.amount}. Sign into the admin panel for more info.\n'
            f'Admin Panel: {admin_url}.\n'
        )

        send_mail(
            email_subject,
            email_body,
            'chinemeremokpara93@gmail.com',
            ['chinemeremokpara93@gmail.com', 'Okaforambrose2020@gmail.com'],
            fail_silently=False
        )

        messages.success(request, 'Your withdrawal request has been submitted successfully. We will process it shortly.')
        return redirect('referral')

    return render(request, 'accounts/referral.html')
