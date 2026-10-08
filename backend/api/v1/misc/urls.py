from django.urls import path

from api.v1.misc.views import ContactView, sentry_tunnel

urlpatterns = [
    path("contact", ContactView.as_view(), name="contact"),
    path("tunnel", sentry_tunnel, name="sentry_tunnel"),
]
