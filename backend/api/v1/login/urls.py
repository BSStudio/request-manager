from django.urls import path

from api.v1.login.views import TokenBlacklistView, TokenObtainPairOAuth2View

urlpatterns = [
    path(
        "login/social",
        TokenObtainPairOAuth2View.as_view(),
        name="social",
    ),
    path("logout", TokenBlacklistView.as_view(), name="logout"),
]
