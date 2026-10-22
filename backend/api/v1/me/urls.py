from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.v1.me.views import (
    MeViewSet,
    NotificationViewSet,
    OAuth2ConnectDisconnectView,
)
from common.rest_framework.routers import DetailOnlyRouter

me_router = DetailOnlyRouter(trailing_slash=False)
me_router.register(r"me", MeViewSet, basename="me")

notification_router = SimpleRouter(trailing_slash=False)
notification_router.register(
    r"me/notifications", NotificationViewSet, basename="notification"
)

urlpatterns = [
    path("", include(me_router.urls)),
    path("", include(notification_router.urls)),
    path(
        "me/social/<str:provider>",
        OAuth2ConnectDisconnectView.as_view(),
        name="social_connect_disconnect",
    ),
]
