# app/subscriptions/serializers.py
from rest_framework import serializers
from .models import UserSubscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = ['product_id', 'active', 'expires_at', 'platform', 'updated_at']

class SubscriptionSyncSerializer(serializers.Serializer):
    product_id = serializers.CharField(required=False, allow_blank=True)
    active = serializers.BooleanField()
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    platform = serializers.ChoiceField(choices=['android', 'ios'], required=False, allow_null=True)