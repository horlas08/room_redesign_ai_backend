from django.urls import path
from .views_ai import RedesignRoomView, HistoryView
from .views_auth import GuestGenerateView, GuestHistoryView

urlpatterns = [
    path('redesign-room/', RedesignRoomView.as_view(), name='redesign-room'),
    path('history/', HistoryView.as_view(), name='history'),
    path('guest/generate/', GuestGenerateView.as_view(), name='guest generate'),
    path('guest/history/', GuestHistoryView.as_view(), name='guest history'),
]
