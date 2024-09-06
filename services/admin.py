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
    list_display = ('id', 'user', 'plan', 'status', 'start_date', 'end_date')
    search_fields = ('user__username', 'plan__name')
    list_filter = ('status',)
    list_per_page = 25
    

admin.site.register(Service, ServiceAdmin) 
admin.site.register(Plan, PlanAdmin)
admin.site.register(Subscription, SubscriptionAdmin)