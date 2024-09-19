from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .models import Service, Plan, Subscription
from accounts.models import Referral
import stripe
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from datetime import timedelta
from django.contrib.auth.models import User
from urllib.parse import quote
import logging
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

# Set up your Stripe secret key
stripe.api_key = settings.STRIPE_SECRET_KEY

def index(request):
    services = Service.objects.all().filter(is_published=True)

    paginator = Paginator(services, 6)
    page = request.GET.get('page')
    paged_services = paginator.get_page(page)

    context = {
        'services': paged_services
    }
    return render(request, 'services/services.html', context)

def service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    plans = service.plans.all()  # Fetch all related plans for this service

    context = {
        'service': service,
        'plans': plans  # Add plans to the context
    }
    return render(request, 'services/service.html', context)

@login_required(login_url='/accounts/login/')  # Redirect to the login page if not authenticated
def process_payment(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        service_id = request.POST.get('service_id')  # Get the service_id from the form

        if plan_id:  # Check if a plan is selected
            plan = get_object_or_404(Plan, id=plan_id)  # Get the selected plan

            if plan.name == "Unlimited Account":
                # One-time payment, no recurring details
                payment_mode = 'payment'
                price_data = {
                    'currency': 'usd',
                    'product_data': {
                        'name': plan.service.name,  # Use the plan's name for the product name
                    },
                    'unit_amount': int(plan.price * Decimal('100')),  # Convert to cents and ensure it's an integer
                }
            else:
                # For all other plans, use subscription mode with recurring intervals
                payment_mode = 'subscription'

                if plan.duration_in_months == 1:
                    interval = 'month'
                elif plan.duration_in_months == 12:
                    interval = 'year'
                else:
                    interval = 'month'  # Default to month, handle as needed

                price_data = {
                    'currency': 'usd',
                    'product_data': {
                        'name': plan.service.name,  # Use the plan's name for the product name
                    },
                    'recurring': {
                        'interval': interval,
                        'interval_count': plan.duration_in_months if interval != 'year' else 1
                    },
                    'unit_amount': int(plan.price * Decimal('100')),  # Convert to cents and ensure it's an integer
                }

            # Create a new Stripe session for payment with the desired name
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': price_data,
                    'quantity': 1,
                }],
                mode=payment_mode,  # Set the payment mode based on the plan
                success_url=request.build_absolute_uri('/services/payment/success/'),
                cancel_url=request.build_absolute_uri(f'/services/{service_id}/'),
                client_reference_id=request.user.username,  # Pass username as a reference
                metadata={'plan_id': plan.id}  # Pass the plan ID in the metadata for later use
            )

            # Save the service_id in the session in case the user cancels
            request.session['service_id'] = service_id

            # Handle referral logic (leave this here as it is not related to subscription creation)
            try:
                referral = Referral.objects.get(referred_user=request.user)
                earnings = plan.price * Decimal('0.4')  # Calculate 40% of the service price
                referral.earnings += earnings
                referral.save()
            except Referral.DoesNotExist:
                pass

            return redirect(session.url, code=303)

    return redirect('service', service_id=request.POST.get('service_id'))

def payment_success(request):
    return render(request, 'services/payment_success.html')

def payment_cancel(request):
    service_id = request.session.get('service_id')
    if service_id:
        # Redirect to the single service page
        return redirect('service', service_id=service_id)
    return redirect('services')  # Fallback in case service_id is not found in the session

def cancel_subscription(request, subscription_id):
    try:
        # Get the specific subscription by ID
        subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user, status='active')
        
        # Immediately cancel the subscription with Stripe
        try:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        except stripe.error.InvalidRequestError as e:
            # Handle case where the subscription does not exist on Stripe
            logger.error(f"Stripe error: {e}")
            messages.error(request, 'Error: Unable to cancel the subscription on Stripe. It may have already been canceled or does not exist.')
            return redirect('dashboard')

        # Update the subscription status in the database to 'canceled'
        subscription.status = 'canceled'
        subscription.end_date = timezone.now()  # Set the end date to the current time
        subscription.save()

        # Render the payment_cancel.html template with the correct service_id context
        return render(request, 'services/payment_cancel.html', {'service_id': subscription.plan.service.id})  # Access service_id via plan.service.id

    except Subscription.DoesNotExist:
        # Handle case where no active subscription is found
        messages.error(request, 'Subscription not found or already canceled.')
        return redirect('dashboard')

    except Exception as e:
        # Handle any other exceptions that may occur
        logger.error(f"Unexpected error: {e}")
        messages.error(request, 'An unexpected error occurred while canceling your subscription. Please try again later.')
        return redirect('dashboard')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
        logger.info(f"Received Stripe event: {event['type']}")
    except ValueError:
        logger.error("Invalid payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        client_reference_id = session.get('client_reference_id')
        plan_id = session['metadata'].get('plan_id')
        
        # Handle the subscription creation
        subscription_id = session.get('subscription')  # Get the subscription ID from Stripe

        try:
            user = User.objects.get(username=client_reference_id)
            plan = Plan.objects.get(id=plan_id)

            # Create or update the subscription
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                plan=plan,
                defaults={
                    'stripe_subscription_id': subscription_id if subscription_id else '',
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timedelta(days=plan.duration_in_months * 30),
                    'status': 'active'
                }
            )
            if not created:
                subscription.status = 'active'
                subscription.stripe_subscription_id = subscription_id if subscription_id else ''
                subscription.end_date = timezone.now() + timedelta(days=plan.duration_in_months * 30)
                subscription.save()

            logger.info(f"Subscription created or updated for user {user.username}")

        except (User.DoesNotExist, Plan.DoesNotExist):
            logger.error("User or Plan does not exist")
            return HttpResponse(status=400)

    return HttpResponse(status=200)





