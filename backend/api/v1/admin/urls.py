from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.v1.admin.projects.views import ProjectAdminViewSet
from api.v1.admin.reports.views import ReportAdminView
from api.v1.admin.todos.views import TodoAdminViewSet

todo_router = SimpleRouter(trailing_slash=False)
todo_router.register(r"todos", TodoAdminViewSet, basename="todo")

project_router = SimpleRouter(trailing_slash=False)
project_router.register(r"projects", ProjectAdminViewSet, basename="project")

urlpatterns = [
    path("", include((todo_router.urls, "todos"), namespace="todos")),
    path("", include((project_router.urls, "projects"), namespace="projects")),
    path("", include(("api.v1.admin.requests.urls", "requests"), namespace="requests")),
    path("", include(("api.v1.admin.users.urls", "users"), namespace="users")),
    path("report", ReportAdminView.as_view(), name="report"),
]
