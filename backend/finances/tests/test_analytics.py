from datetime import datetime, timezone
from decimal import Decimal

from django.test import TestCase

from finances import analytics
from finances.models import Transaction


def _txn(direction, amount, category="other", month=1):
    return Transaction(
        direction=direction, amount=Decimal(amount), category=category,
        occurred_at=datetime(2026, month, 15, 12, 0, tzinfo=timezone.utc),
    )


class AnalyticsTests(TestCase):
    def test_period_summary_and_rates(self):
        txns = [
            _txn("in", 1000), _txn("in", 500),
            _txn("out", 300), _txn("out", 200),
        ]
        p = analytics.period_summary(txns)
        self.assertEqual(p.money_in, Decimal("1500.00"))
        self.assertEqual(p.money_out, Decimal("500.00"))
        self.assertEqual(p.net, Decimal("1000.00"))
        self.assertAlmostEqual(analytics.savings_rate(p), 66.6667, places=2)
        self.assertAlmostEqual(analytics.spend_pace(p), 33.3333, places=2)

    def test_category_breakdown_sorted_desc(self):
        txns = [
            _txn("out", 800, "food"), _txn("out", 200, "transport"),
            _txn("in", 5000, "salary"),  # income excluded from breakdown
        ]
        rows = analytics.category_breakdown(txns)
        self.assertEqual(rows[0]["category"], "food")
        self.assertEqual(rows[0]["pct"], 80.0)
        self.assertEqual(rows[1]["category"], "transport")

    def test_health_score_rewards_realistic_savings(self):
        # 30% savings, low concentration, positive trend -> excellent.
        p = analytics.Period(Decimal("1000"), Decimal("700"), 10)
        score = analytics.health_score(p, concentration_pct=25.0, net_trend_positive=True)
        self.assertGreaterEqual(score, 80)
        # Overspending -> poor.
        p2 = analytics.Period(Decimal("1000"), Decimal("1200"), 10)
        self.assertLess(analytics.health_score(p2, 90.0, False), 30)

    def test_net_trend_positive_uses_halves(self):
        series = [
            {"net": "-100"}, {"net": "-50"}, {"net": "0"},
            {"net": "100"}, {"net": "200"}, {"net": "300"},
        ]
        self.assertTrue(analytics.net_trend_positive(series))
        self.assertFalse(analytics.net_trend_positive(list(reversed(series))))
