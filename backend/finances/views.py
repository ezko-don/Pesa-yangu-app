from __future__ import annotations

import csv
from decimal import Decimal

from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from . import analytics
from .models import Budget, Goal, Transaction
from .serializers import (
    BudgetSerializer,
    GoalSerializer,
    SyncSerializer,
    TransactionSerializer,
)
from .sync import ingest_raw_messages


class OwnedModelViewSet(viewsets.ModelViewSet):
    """Restricts all queries + writes to the authenticated user."""

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class TransactionViewSet(OwnedModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if (q := params.get("search")):
            qs = qs.filter(description__icontains=q)
        if (cat := params.get("category")) and cat != "all":
            qs = qs.filter(category=cat)
        if (direction := params.get("type")) in {"in", "out"}:
            qs = qs.filter(direction=direction)
        source = params.get("source")
        if source == "auto":
            qs = qs.filter(source_type__in=[
                Transaction.SourceType.MPESA_SMS, Transaction.SourceType.BANK_SMS])
        elif source == "manual":
            qs = qs.filter(source_type=Transaction.SourceType.MANUAL)
        return qs

    @action(detail=False, methods=["get"])
    def summary(self, request):
        p = analytics.period_summary(self.get_queryset())
        docs = self.get_queryset().filter(
            source_type=Transaction.SourceType.RECEIPT).count()
        return Response({
            "money_in": str(p.money_in),
            "money_out": str(p.money_out),
            "count": p.count,
            "documents_parsed": docs,
        })

    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = "attachment; filename=transactions.csv"
        writer = csv.writer(resp)
        writer.writerow(["Date", "Description", "Category", "Direction", "Amount", "Source"])
        for t in self.get_queryset():
            writer.writerow([
                t.occurred_at.date(), t.description, t.get_category_display(),
                t.direction, t.amount, t.source_institution or t.get_source_type_display(),
            ])
        return resp


class BudgetViewSet(OwnedModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer

    @action(detail=False, methods=["get"])
    def summary(self, request):
        budgets = self.get_queryset()
        total_budgeted = sum((b.monthly_limit for b in budgets), Decimal(0))
        on_track = 0
        over_amount = Decimal(0)
        total_spent = Decimal(0)
        for b in budgets:
            spent = _budget_spent(request.user, b.category)
            total_spent += spent
            if spent > b.monthly_limit:
                over_amount += spent - b.monthly_limit
            else:
                on_track += 1
        return Response({
            "total_budgeted": str(total_budgeted),
            "total_spent": str(total_spent),
            "on_track": on_track,
            "over_budget_amount": str(over_amount),
        })

    @action(detail=False, methods=["get"])
    def suggest(self, request):
        """AI-suggested amount from the 3-month spending average (spec 3.4 BETTER)."""
        category = request.query_params.get("category")
        if not category:
            return Response({"suggested": None})
        since = timezone.now() - timezone.timedelta(days=90)
        agg = Transaction.objects.filter(
            user=request.user, category=category,
            direction=Transaction.Direction.OUT, occurred_at__gte=since,
        ).aggregate(total=Sum("amount"))
        total = agg["total"] or Decimal(0)
        avg = (total / 3).quantize(Decimal("1")) if total else Decimal(0)
        return Response({
            "category": category,
            "suggested": str(avg),
            "basis": "3-month SMS spending average",
        })


def _budget_spent(user, category) -> Decimal:
    today = timezone.now()
    agg = Transaction.objects.filter(
        user=user, category=category, direction=Transaction.Direction.OUT,
        occurred_at__year=today.year, occurred_at__month=today.month,
    ).aggregate(total=Sum("amount"))
    return agg["total"] or Decimal(0)


class GoalViewSet(OwnedModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer

    @action(detail=False, methods=["get"])
    def summary(self, request):
        goals = self.get_queryset()
        active = [g for g in goals if not g.is_completed]
        return Response({
            "active_goals": len(active),
            "total_saved": str(sum((g.saved_amount for g in goals), Decimal(0))),
            "total_target": str(sum((g.target_amount for g in goals), Decimal(0))),
            "completed": sum(1 for g in goals if g.is_completed),
        })


class SyncView(APIView):
    """Dev/testing: POST raw SMS strings; they are parsed + ingested."""

    def post(self, request):
        serializer = SyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ingest_raw_messages(request.user, serializer.validated_data["messages"])
        return Response(result, status=status.HTTP_201_CREATED)


class DashboardView(APIView):
    """Home Dashboard payload (spec 3.2)."""

    def get(self, request):
        txns = list(Transaction.objects.filter(user=request.user))
        p = analytics.period_summary(txns)
        cashflow = analytics.monthly_cashflow(txns, months=6)
        concentration = analytics.spend_concentration(txns)
        trend_up = analytics.net_trend_positive(cashflow)
        score = analytics.health_score(p, concentration["pct"], trend_up)
        sr = analytics.savings_rate(p)
        avg_monthly_expense = p.money_out if p.money_out > 0 else Decimal(1)
        runway = analytics.emergency_runway_months(p, avg_monthly_expense / max(len(cashflow), 1))
        sources = request.user.sms_sources.filter(enabled=True)
        return Response({
            "money_in": str(p.money_in),
            "money_out": str(p.money_out),
            "net_cash_flow": str(p.net),
            "transactions": p.count,
            "health_score": score,
            "savings_rate": round(sr, 1),
            "spend_pace": round(analytics.spend_pace(p), 1),
            "signals": {
                "save": "healthy" if sr >= 20 else "watch",
                "spend_concentration": concentration,
                "emergency_runway_months": runway,
            },
            "auto_sync": {
                "active": sources.exists(),
                "sources": [s.name for s in sources],
                "today_count": txns_today(request.user),
            },
        })


def txns_today(user) -> int:
    today = timezone.now()
    return Transaction.objects.filter(
        user=user, created_at__year=today.year, created_at__month=today.month,
        created_at__day=today.day,
    ).count()


class ReportsView(APIView):
    """Reports payload: health cards + cash-flow trend + category breakdown (spec 3.6)."""

    def get(self, request):
        txns = list(Transaction.objects.filter(user=request.user))
        p = analytics.period_summary(txns)
        cashflow = analytics.monthly_cashflow(txns, months=6)
        breakdown = analytics.category_breakdown(txns)
        concentration = analytics.spend_concentration(txns)
        trend_up = analytics.net_trend_positive(cashflow)
        return Response({
            "health_score": analytics.health_score(p, concentration["pct"], trend_up),
            "net_cash_flow": str(p.net),
            "savings_rate": round(analytics.savings_rate(p), 1),
            "spend_pace": round(analytics.spend_pace(p), 1),
            "cashflow_trend": cashflow,
            "average_monthly_margin": analytics.average_monthly_margin(cashflow),
            "category_breakdown": breakdown,
            "signals": {
                "save": "healthy" if analytics.savings_rate(p) >= 20 else "watch",
                "spend_concentration": concentration,
            },
        })
