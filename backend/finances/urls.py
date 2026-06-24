from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BudgetViewSet,
    DashboardView,
    GoalViewSet,
    ReportsView,
    SyncView,
    TransactionViewSet,
)

router = DefaultRouter()
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("budgets", BudgetViewSet, basename="budget")
router.register("goals", GoalViewSet, basename="goal")

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("reports/", ReportsView.as_view(), name="reports"),
    path("sync/", SyncView.as_view(), name="sync"),
    path("", include(router.urls)),
]
