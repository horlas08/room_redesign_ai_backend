# app/subscriptions/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from django.utils import timezone
from .models import UserSubscription
from .serializers import SubscriptionSerializer, SubscriptionSyncSerializer

class SubscriptionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub, _ = UserSubscription.objects.get_or_create(user=request.user)
        # Optional auto-expiry check
        if sub.expires_at and sub.expires_at < timezone.now():
            sub.active = False
            sub.save(update_fields=['active'])
        return Response({
            'is_pro': bool(sub.active),
            'subscription': SubscriptionSerializer(sub).data
        })

class SubscriptionSyncView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSyncSerializer

    def post(self, request):
        # NOTE: This is a simple “external registration” approach.
        # In production, verify purchase server-side with Google/Apple before trusting client.
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sub, _ = UserSubscription.objects.get_or_create(user=request.user)
        sub.active = ser.validated_data['active']
        sub.product_id = ser.validated_data.get('product_id', sub.product_id)
        sub.platform = ser.validated_data.get('platform', sub.platform) or ''
        sub.expires_at = ser.validated_data.get('expires_at', sub.expires_at)
        sub.save()
        return Response({
            'is_pro': bool(sub.active),
            'subscription': SubscriptionSerializer(sub).data
        }, status=status.HTTP_200_OK)