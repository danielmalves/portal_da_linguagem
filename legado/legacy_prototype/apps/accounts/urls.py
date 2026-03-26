from django.urls import path
from django.contrib.auth.views import LogoutView, LoginView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
]
