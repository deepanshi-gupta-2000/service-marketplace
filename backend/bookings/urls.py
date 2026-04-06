from django.urls import path
from .views import BookingView, ServiceRequestView
# from .views import MyBookingsView, ProviderBookingsView, UpdateBookingStatusView

urlpatterns = [
    path('', BookingView.as_view()),
    path('bookings/', BookingView.as_view()),
    path('requests/', ServiceRequestView.as_view()),
    # path('my-bookings/', MyBookingsView.as_view()),
    # path('provider-bookings/', ProviderBookingsView.as_view()),
    # path('bookings/<int:pk>/', UpdateBookingStatusView.as_view()),
]
