from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Referral(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals')
    referred_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referred_by')
    referral_code = models.CharField(max_length=100, unique=True)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    credited = models.BooleanField(default=False)  # Tracks whether the earnings have been credited

    def clean(self):
        # Prevent self-referral
        if self.referrer == self.referred_user:
            raise ValidationError("A user cannot refer themselves.")

    def __str__(self):
        return f"{self.referred_user.username}"

class Withdrawal(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('paypal', 'PayPal'),
        ('crypto', 'Crypto'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15, null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=[('paypal', 'PayPal'), ('crypto', 'Crypto')], default='paypal')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    # Fields specific to PayPal
    paypal_username = models.CharField(max_length=255, null=True, blank=True)

    # Fields specific to Crypto
    crypto_coin = models.CharField(max_length=50, null=True, blank=True)
    crypto_wallet_address = models.CharField(max_length=255, null=True, blank=True)


    def __str__(self):
        return f"Withdrawal Request by {self.user.username} - {self.payment_method} - ${self.amount} USD"