from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.v1.admin.reports.views import ReportAdminView
from api.v1.admin.todos.views import TodoAdminViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r"todos", TodoAdminViewSet, basename="todo")

urlpatterns = [
    path("", include((router.urls, "todos"), namespace="todos")),
    path("", include(("api.v1.admin.requests.urls", "requests"), namespace="requests")),
    path("", include(("api.v1.admin.users.urls", "users"), namespace="users")),
    path("report", ReportAdminView.as_view(), name="report"),
]
