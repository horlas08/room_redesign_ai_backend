from django.urls import path
from .views_ai import RedesignRoomView, HistoryView

urlpatterns = [
    path('redesign-room/', RedesignRoomView.as_view(), name='redesign-room'),
    path('history/', HistoryView.as_view(), name='history'),
]
