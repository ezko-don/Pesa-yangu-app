from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from .models import Budget, Goal, Transaction


class TransactionSerializer(serializers.ModelSerializer):
    source_badge = serializers.SerializerMethodField()
    is_auto_synced = serializers.BooleanField(read_only=True)
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id", "description", "amount", "direction", "category", "category_label",
            "occurred_at", "source_type", "source_institution", "source_badge",
            "is_auto_synced", "reference", "balance_after", "confidence",
        ]
        read_only_fields = ["confidence", "balance_after"]

    def get_source_badge(self, obj: Transaction) -> str:
        if obj.source_type == Transaction.SourceType.MPESA_SMS:
            return "M-Pesa SMS"
        if obj.source_type == Transaction.SourceType.BANK_SMS:
            return f"{obj.source_institution} SMS" if obj.source_institution else "Bank SMS"
        return obj.get_source_type_display()

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        validated_data.setdefault("source_type", Transaction.SourceType.MANUAL)
        return super().create(validated_data)


def _spent_this_month(user, category: str) -> Decimal:
    today = timezone.now()
    agg = Transaction.objects.filter(
        user=user,
        category=category,
        direction=Transaction.Direction.OUT,
        occurred_at__year=today.year,
        occurred_at__month=today.month,
    ).aggregate(total=Sum("amount"))
    return agg["total"] or Decimal(0)


class BudgetSerializer(serializers.ModelSerializer):
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    pct_used = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Budget
        fields = [
            "id", "name", "category", "category_label", "monthly_limit",
            "spent", "remaining", "pct_used", "status",
        ]

    def _spent(self, obj: Budget) -> Decimal:
        return _spent_this_month(obj.user, obj.category)

    def get_spent(self, obj):
        return str(self._spent(obj))

    def get_remaining(self, obj):
        return str(max(Decimal(0), obj.monthly_limit - self._spent(obj)))

    def get_pct_used(self, obj):
        if obj.monthly_limit <= 0:
            return 0.0
        return round(float(self._spent(obj) / obj.monthly_limit * 100), 1)

    def get_status(self, obj):
        return "over_budget" if self._spent(obj) > obj.monthly_limit else "on_track"

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class GoalSerializer(serializers.ModelSerializer):
    progress_pct = serializers.FloatField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            "id", "title", "goal_type", "target_amount", "saved_amount",
            "target_date", "priority", "progress_pct", "is_completed", "status",
        ]

    def get_status(self, obj: Goal) -> str:
        if obj.is_completed:
            return "completed"
        if not obj.target_date:
            return "on_track"
        today = date.today()
        total_days = (obj.target_date - obj.created_at.date()).days if obj.created_at else 0
        if total_days <= 0:
            return "on_track" if obj.progress_pct >= 100 else "at_risk"
        elapsed = (today - obj.created_at.date()).days
        expected_pct = min(100.0, max(0.0, elapsed / total_days * 100))
        delta = obj.progress_pct - expected_pct
        if delta >= 10:
            return "ahead"
        if delta >= -5:
            return "on_track"
        if delta >= -20:
            return "behind"
        return "at_risk"

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class SyncSerializer(serializers.Serializer):
    """Dev/testing path: accept raw SMS strings to parse server-side."""
    messages = serializers.ListField(child=serializers.CharField(), allow_empty=False)
