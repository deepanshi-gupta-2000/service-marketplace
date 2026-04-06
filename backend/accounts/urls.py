from django.urls import path
from .views import CaseInsensitiveLoginView, CurrentUserView, RegisterView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", CaseInsensitiveLoginView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("me/", CurrentUserView.as_view()),
]
