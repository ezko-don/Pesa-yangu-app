from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from finances.models import Budget, Goal, Transaction

User = get_user_model()


class ApiAuthTests(APITestCase):
    def test_register_login_and_me(self):
        r = self.client.post("/api/auth/register/", {
            "email": "a@b.com", "first_name": "Ann", "password": "secret123",
        }, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIn("access", r.data["tokens"])

        r = self.client.post("/api/auth/login/", {
            "email": "a@b.com", "password": "secret123",
        }, format="json")
        self.assertEqual(r.status_code, 200)
        token = r.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        r = self.client.get("/api/auth/me/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["email"], "a@b.com")

    def test_unauthenticated_blocked(self):
        self.assertEqual(self.client.get("/api/dashboard/").status_code, 401)


class ApiDataTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="u@x.com", email="u@x.com", password="secret123"
        )
        self.client.force_authenticate(self.user)

    def test_sync_parses_and_ingests_mpesa_sms(self):
        sms = ("TKA2B3CD45 Confirmed. Ksh2,340 sent to NAIVAS SUPERMARKET 456789 "
               "on 7/6/26 at 8:23 AM. New M-PESA balance is Ksh12,450")
        r = self.client.post("/api/sync/", {"messages": [sms]}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["created"], 1)
        # Idempotent: same SMS is deduped by fingerprint.
        r2 = self.client.post("/api/sync/", {"messages": [sms]}, format="json")
        self.assertEqual(r2.data["skipped_duplicates"], 1)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 1)

    def test_dashboard_and_reports_shape(self):
        Transaction.objects.create(
            user=self.user, description="Salary", amount=Decimal("50000"),
            direction="in", category="salary", occurred_at="2026-06-01T09:00:00Z",
        )
        Transaction.objects.create(
            user=self.user, description="Naivas", amount=Decimal("2000"),
            direction="out", category="food", occurred_at="2026-06-02T09:00:00Z",
        )
        d = self.client.get("/api/dashboard/").data
        for key in ["health_score", "savings_rate", "money_in", "money_out", "signals"]:
            self.assertIn(key, d)
        rep = self.client.get("/api/reports/").data
        self.assertIn("cashflow_trend", rep)
        self.assertIn("category_breakdown", rep)

    def test_budget_suggest_uses_history(self):
        for _ in range(3):
            Transaction.objects.create(
                user=self.user, description="Food", amount=Decimal("3000"),
                direction="out", category="food", occurred_at="2026-06-02T09:00:00Z",
            )
        r = self.client.get("/api/budgets/suggest/", {"category": "food"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Decimal(r.data["suggested"]), Decimal("3000"))

    def test_goal_progress_serialized(self):
        Goal.objects.create(
            user=self.user, title="Trip", target_amount=Decimal("1000"),
            saved_amount=Decimal("250"),
        )
        r = self.client.get("/api/goals/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data[0]["progress_pct"], 25.0)

    def test_transactions_filter_by_source(self):
        Transaction.objects.create(
            user=self.user, description="Auto", amount=Decimal("100"),
            direction="out", category="food", occurred_at="2026-06-02T09:00:00Z",
            source_type="mpesa_sms",
        )
        Transaction.objects.create(
            user=self.user, description="Manual", amount=Decimal("100"),
            direction="out", category="food", occurred_at="2026-06-02T09:00:00Z",
            source_type="manual",
        )
        r = self.client.get("/api/transactions/", {"source": "auto"})
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]["description"], "Auto")


class HelaTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="h@x.com", email="h@x.com", password="secret123"
        )
        self.client.force_authenticate(self.user)

    def test_chat_logs_transaction_from_natural_language(self):
        r = self.client.post("/api/hela/chat/", {
            "message": "I bought juice 200 and data 80",
        }, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data["logged"]), 2)
        self.assertTrue(
            Transaction.objects.filter(user=self.user, source_type="chat").exists()
        )
