from django.contrib import admin
from .models import Service, Plan, Subscription
# Register your models here.

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_published')
    list_display_links = ('id', 'name')
    list_filter = ('name',)
    list_editable = ('is_published',)
    search_fields = ('name',)
    list_per_page = 25

class PlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'duration_in_months', 'price')
    list_display_links = ('id', 'service')
    list_filter = ('service',)
    search_fields = ('service', 'duration_in_months', 'price')
    list_per_page = 25

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'start_date', 'end_date', 'status')  # Added 'status' to list_display
    list_display_links = ('id', 'plan')  # Allow linking to plan from id and plan
    search_fields = ('plan__name', 'user__username')  # Allow searching by plan name and user
    list_filter = ('status',)  # Add filter by subscription status (active, canceled, etc.)
    list_per_page = 25  # Pagination

    def get_queryset(self, request):
        # Override the default queryset to only show active subscriptions by default
        qs = super().get_queryset(request)
        return qs.filter(status='active')
    

admin.site.register(Service, ServiceAdmin) 
admin.site.register(Plan, PlanAdmin)
admin.site.register(Subscription, SubscriptionAdmin)