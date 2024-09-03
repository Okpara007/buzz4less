from django.shortcuts import render
from django.http import HttpResponse
from services.models import Service

def index(request):
    services = Service.objects.all().filter(is_published=True)[:3]

    context = {
        'services': services
    }
    return render(request, 'pages/index.html', context)

def about(request):
    return render(request, 'pages/about.html')

