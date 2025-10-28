from django.conf import settings
from django.db import models

# app/subscriptions/models.py

class UserSubscription(models.Model):
    PLATFORM_CHOICES = (('android', 'Android'), ('ios', 'iOS'))
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    product_id = models.CharField(max_length=128, blank=True, default='')
    active = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    platform = models.CharField(max_length=16, choices=PLATFORM_CHOICES, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user} | {self.product_id} | active={self.active}'