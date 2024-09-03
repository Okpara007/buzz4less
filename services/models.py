from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Service(models.Model):
    name = models.CharField(max_length=100)
    pre_description = models.TextField(blank=True, null=True)
    main_description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='photos/%Y/%m/%d/', blank=True, null=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Plan(models.Model):
    service = models.ForeignKey(Service, on_delete=models.DO_NOTHING, related_name='plans')
    name = models.CharField(max_length=100)
    duration_in_months = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Changed to DecimalField for currency
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.service.name} - {self.name}"

class Subscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.DO_NOTHING, related_name='subscriptions')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)  # Added this field

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_in_months * 30)
        super().save(*args, **kwargs)

    def cancel(self):
        self.status = 'canceled'
        self.end_date = timezone.now()  # Optionally, set the end_date to the current time
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.plan.service.name})"
