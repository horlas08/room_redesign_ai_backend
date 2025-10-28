# app/subscriptions/urls.py
from django.urls import path
from .views import SubscriptionView, SubscriptionSyncView

urlpatterns = [
    path('subscription/', SubscriptionView.as_view(), name='subscription'),
    path('subscription/sync/', SubscriptionSyncView.as_view(), name='subscription-sync'),
]