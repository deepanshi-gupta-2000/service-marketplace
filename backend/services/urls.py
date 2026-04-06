from django.urls import path

from .views import (
    ProviderDashboardView,
    ProviderProfileView,
    ServiceListView,
    ServiceProviderDetailView,
    ServiceProviderView,
)

urlpatterns = [
    path("services/", ServiceListView.as_view()),
    path("providers/", ServiceProviderView.as_view()),
    path("providers/<int:provider_id>/", ServiceProviderDetailView.as_view()),
    path("providers/dashboard/", ProviderDashboardView.as_view()),
    path("providers/profile/", ProviderProfileView.as_view()),
]
