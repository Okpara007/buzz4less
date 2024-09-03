from django.db import models
from datetime import datetime

class Contact(models.Model):
    name = models.CharField(max_length=200, blank=True)
    email = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True, null=True)
    contact_date = models.DateTimeField(default=datetime.now, blank=True)
    user_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name
