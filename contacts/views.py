from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Contact
from django.core.mail import send_mail

# Create your views here.
def contact(request):
    if request.method == 'POST':
        # Extract common fields from POST request
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', None)
        message = request.POST.get('message', None)
        
        # Determine if the user is authenticated
        user_id = request.user.id if request.user.is_authenticated else None

        new_contact = Contact(
            name=name, 
            email=email, 
            phone=phone, 
            message=message, 
            user_id=user_id,
        )
        new_contact.save()

        # Prepare and send the email notification
        email_subject = f'A contact has been made.'
        admin_url = 'https://buzzforless.com/admin/'  # Local admin URL
        email_body = (
            f'{name}.\n'
            f'There has been a contact. Sign into the admin panel for more info.\n'
            f'Admin Panel: {admin_url}.\n'
            f'{new_contact.message}'
        )

        send_mail(
            email_subject,
            email_body,
            'reset_account@buzzforless.com',
            [ 'reset_account@buzzforless.com', 'chinemeremokpara93@gmail.com', 'Okaforambrose2020@gmail.com'],
            fail_silently=False
        )

    return render(request, 'contacts/contacts.html')