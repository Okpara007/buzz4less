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
                client_reference_id=request.user.username  # Set the name to appear in the checkout page
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
        stripe.Subscription.delete(subscription.stripe_subscription_id)  # Assuming stripe_subscription_id is stored in Plan or Subscription model

        # Update the subscription status in the database to 'canceled'
        subscription.status = 'canceled'
        subscription.end_date = timezone.now()  # Set the end date to the current time
        subscription.save()

        # Redirect or inform the user that their subscription has been canceled
        return redirect('/subscription/canceled/')  # Redirect to a confirmation page
    except Subscription.DoesNotExist:
        # If no active subscription is found, redirect or show an error
        return redirect('/dashboard/')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        subscription_id = invoice['subscription']
        customer_id = invoice['customer']

        # Get the user associated with the Stripe session
        try:
            user = User.objects.get(username=event['data']['object']['client_reference_id'])
            plan = Plan.objects.get(stripe_subscription_id=subscription_id)
            Subscription.objects.create(
                user=user,
                plan=plan,
                stripe_subscription_id=subscription_id,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=plan.duration_in_months * 30),
                status='active'
            )
        except (User.DoesNotExist, Plan.DoesNotExist):
            pass  # Handle cases where user or plan is not found

    # Handle other event types as needed
    return HttpResponse(status=200)
