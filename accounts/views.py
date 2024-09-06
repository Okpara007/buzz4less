from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .models import Referral
from .models import Withdrawal
from services.models import Subscription
from services.models import Plan
from django.db.models import Sum
import uuid
from django.db import transaction
from django.core.mail import send_mail
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def generate_referral_code():
    while True:
        code = str(uuid.uuid4()).replace("-", "")[:10]
        if not Referral.objects.filter(referral_code=code).exists():
            return code

@transaction.atomic
def signup(request):
    if request.method == 'POST':
        # Collect data from the form
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

        # Create the user
        user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)

        # Handle referral logic
        if referral_code:
            try:
                # Fetch the referral entry using the referral code
                referral_entry = Referral.objects.get(referral_code=referral_code)
                referrer = referral_entry.referred_user  # Ensure this points to the correct referred_user

                # Ensure no duplicate entry for referred_user
                if not Referral.objects.filter(referred_user=user).exists():
                    # Assign referrer and generate a new referral code for the new user
                    Referral.objects.create(referrer=referrer, referred_user=user, referral_code=generate_referral_code())
            except Referral.DoesNotExist:
                # Handle invalid referral code case here if needed
                return JsonResponse({'error': 'Invalid referral code.'}, status=400)
        else:
            # Create a self-referral entry if no referral code is provided
            Referral.objects.create(referrer=user, referred_user=user, referral_code=generate_referral_code())

        # Log in the user immediately after signup
        auth_login(request, user)
        return JsonResponse({'success': 'Account created successfully and logged in.'}, status=200)

    return render(request, 'accounts/login.html')


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Authenticate the user
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
    # Fetch only active subscriptions
    subscriptions = Subscription.objects.filter(user=user, status='active').order_by('-start_date')

    context = {
        'subscriptions': subscriptions,
    }
    return render(request, 'accounts/dashboard.html', context)



@login_required
def referral(request):
    user = request.user
    
    # Get the referral entry for the current user
    referral = Referral.objects.filter(referred_user=user).first()
    
    # If no referral entry exists, create a self-referral entry
    if not referral:
        referral = Referral.objects.create(referrer=user, referred_user=user, referral_code=generate_referral_code())

    # Get the users referred by the current user
    referred_users = Referral.objects.filter(referrer=user).exclude(referred_user=user)
    
    # Calculate total earnings
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
        # Extract data from POST request
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', None)
        payment_method = request.POST.get('payment_method')
        amount = request.POST.get('number')

        try:
            # Convert the amount to a float for comparison
            amount = float(amount)
        except ValueError:
            # Handle the case where amount is not a valid number
            messages.error(request, 'Invalid amount entered. Please enter a valid number.')
            return redirect('referral')

        # Calculate total earnings
        total_earnings = Referral.objects.filter(referrer=request.user).aggregate(Sum('earnings'))['earnings__sum'] or 0.00

        # Validate the minimum withdrawal amount
        if amount < 10:
            messages.error(request, 'The minimum amount to withdraw is $10. Please enter a valid amount.')
            return redirect('referral')  # Redirect back to the form

        # Validate that the withdrawal amount does not exceed total earnings
        if amount > total_earnings:
            messages.error(request, 'You cannot withdraw more than your total earnings. Please enter a valid amount.')
            return redirect('referral')  # Redirect back to the form

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

        # Prepare and send the email notification
        email_subject = f'{new_withdrawal.payment_method} withdrawal'
        admin_url = 'https://127.0.0.1:8000/admin/'  # Local admin URL
        email_body = (
            f'{name}.\n'
            f'There has been a withdrawal request of ${new_withdrawal.amount}. Sign into the admin panel for more info.\n'
            f'Admin Panel: {admin_url}.\n'
            # f'{new_withdrawal.payment_method}'
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

    return render(request, 'accounts/referral.html')  # This should be the correct template