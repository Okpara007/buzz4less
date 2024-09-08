from django.contrib import admin
from .models import Referral, Withdrawal, Profile

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user', 'earnings', 'credited')  # Columns to display
    list_filter = ('credited',)  # Add a filter for credited status
    search_fields = ('referrer__username', 'referred_user__username')  # Add search functionality

    # Add functionality to update credited status directly from the admin panel
    actions = ['mark_as_credited']

    def mark_as_credited(self, request, queryset):
        """Custom admin action to mark selected referrals as credited."""
        rows_updated = queryset.update(credited=True)
        self.message_user(request, f'{rows_updated} referrals were successfully marked as credited.')

    mark_as_credited.short_description = "Mark selected referrals as credited"

@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'amount')
    list_display_links = ('id', 'name')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'verification_code', 'is_verified', 'verification_code_expires_at')
    list_display_links = ('id', 'user')