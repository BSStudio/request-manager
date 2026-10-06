from django.urls import path

from api.v1.login.views import LogoutView, SocialLoginView

urlpatterns = [
    path(
        "login/social",
        SocialLoginView.as_view(),
        name="social",
    ),
    path("logout", LogoutView.as_view(), name="logout"),
]
