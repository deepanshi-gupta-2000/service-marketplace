from django.urls import path
# from .views import ServiceListView

# urlpatterns = [
#     path('', ServiceListView.as_view()),
# ]

from .views import ServiceListView, ServiceProviderView

urlpatterns = [
    path('services/', ServiceListView.as_view()),
    path('providers/', ServiceProviderView.as_view()),
]