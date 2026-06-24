"""Seed a demo account (Esther Zawadi) matching the wireframes.

Run: python manage.py seed_demo
Creates user demo@pesayangu.co.ke / password 'pesayangu' with ~847 auto-synced
M-Pesa + bank transactions, budgets, goals, SMS sources, chat and notifications.
"""
from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import SmsSource
from finances.models import Budget, Goal, Transaction
from hela.models import ChatMessage, Notification

User = get_user_model()

DEMO_EMAIL = "demo@pesayangu.co.ke"
DEMO_PASSWORD = "pesayangu"

# (description, category, [min, max], weight) for expense generation.
# Weights/amounts are tuned so Food & Dining is the top category (~40%) without
# overwhelming the rest, keeping the demo's spend concentration realistic.
EXPENSE_MERCHANTS = [
    ("Naivas Supermarket", "food", (150, 1500), 10),
    ("Java House Kenya", "food", (250, 900), 6),
    ("Mama Mboga", "food", (50, 400), 20),
    ("Bolt", "transport", (120, 700), 10),
    ("Little Cab", "transport", (150, 650), 4),
    ("Matatu", "transport", (50, 150), 24),
    ("Shell", "transport", (1500, 3500), 1),
    ("Safaricom Airtime", "utilities", (20, 200), 20),
    ("Safaricom Data", "utilities", (50, 300), 12),
    ("Kenya Power", "utilities", (800, 2200), 2),
    ("Nairobi Water", "utilities", (300, 900), 2),
    ("Carrefour", "shopping", (300, 2500), 4),
    ("Jumia", "shopping", (500, 4000), 2),
    ("Netflix", "entertainment", (1100, 1100), 1),
    ("DSTV", "entertainment", (1500, 1500), 1),
    ("Cinema", "entertainment", (500, 1500), 2),
    ("Goodlife Pharmacy", "health", (200, 1500), 3),
    ("Text Book Centre", "education", (300, 2000), 1),
]


class Command(BaseCommand):
    help = "Seed the demo Pesa Yangu account."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo data first.")

    def handle(self, *args, **options):
        random.seed(254)  # deterministic demo
        user, created = User.objects.get_or_create(
            email=DEMO_EMAIL,
            defaults=dict(
                username=DEMO_EMAIL, first_name="Esther", last_name="Zawadi",
                email_verified=True, account_type=User.AccountType.INDIVIDUAL,
                phone="+254712345678", two_factor_enabled=True, biometric_enabled=True,
                whatsapp_connected=True,
            ),
        )
        user.set_password(DEMO_PASSWORD)
        user.save()

        if options["reset"] or not created:
            user.transactions.all().delete()
            user.budgets.all().delete()
            user.goals.all().delete()
            user.sms_sources.all().delete()
            user.chat_messages.all().delete()
            user.notifications.all().delete()

        now = timezone.now()
        self._seed_sources(user, now)
        count = self._seed_transactions(user, now)
        self._seed_budgets(user)
        self._seed_goals(user, now)
        self._seed_chat(user)
        self._seed_notifications(user)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded demo account {DEMO_EMAIL} (password '{DEMO_PASSWORD}') with {count} transactions."
        ))

    def _seed_sources(self, user, now):
        SmsSource.objects.bulk_create([
            SmsSource(user=user, name="M-Pesa", short_code="MP", transaction_count=847,
                      last_sync_at=now),
            SmsSource(user=user, name="Equity Bank", short_code="EQ", transaction_count=213,
                      last_sync_at=now - timedelta(minutes=2)),
            SmsSource(user=user, name="KCB Bank", short_code="KCB", transaction_count=98,
                      last_sync_at=now - timedelta(minutes=5)),
            SmsSource(user=user, name="Airtel Money", short_code="AM", transaction_count=0,
                      last_sync_at=now - timedelta(days=1)),
            SmsSource(user=user, name="Co-op Bank", short_code="CO",
                      status=SmsSource.Status.NOT_CONNECTED, enabled=False),
        ])

    # Sources of regular income (description, [min, max] per receipt, weight).
    INCOME_SENDERS = [
        ("Salary - Acme Ltd", "salary", (62000, 68000), 0),  # handled separately
        ("Catatu Logistics", "business", (8000, 22000), 6),
        ("Client Payment", "business", (3000, 18000), 10),
        ("Received - John M.", "transfer", (500, 6000), 24),
        ("Received - Mary W.", "transfer", (500, 4500), 20),
        ("Chama Payout", "business", (5000, 15000), 3),
    ]

    def _seed_transactions(self, user, now) -> int:
        """Generate ~847 auto-synced transactions.

        Expenses are realistic and food-dominated; income is sized so the
        savings rate / health score land in the healthy range shown in the
        wireframes (~25% savings, health in the 80s).
        """
        TARGET_TOTAL = 847
        TARGET_SAVINGS_RATE = 0.25  # money kept / money in

        # --- expenses (food-dominated) ---
        weighted = []
        for name, cat, rng, weight in EXPENSE_MERCHANTS:
            weighted += [(name, cat, rng)] * weight
        n_expense = 480
        expense_rows = []
        total_expense = Decimal(0)
        for _ in range(n_expense):
            name, cat, (lo, hi) = random.choice(weighted)
            amount = Decimal(random.randint(lo, hi))
            total_expense += amount
            # Skew expenses slightly toward older months -> gently improving trend.
            days_ago = int(178 * (random.random() ** 0.7))
            when = now - timedelta(days=days_ago,
                                   hours=random.randint(0, 23), minutes=random.randint(0, 59))
            is_mpesa = name.startswith("Safaricom") or random.random() < 0.7
            expense_rows.append(Transaction(
                user=user, description=name, amount=amount,
                direction=Transaction.Direction.OUT, category=cat, occurred_at=when,
                source_type=Transaction.SourceType.MPESA_SMS if is_mpesa else Transaction.SourceType.BANK_SMS,
                source_institution="M-Pesa" if is_mpesa else random.choice(["Equity Bank", "KCB Bank"]),
                reference=_ref(), balance_after=Decimal(random.randint(2000, 90000)),
                confidence=round(random.uniform(0.93, 0.99), 2), sms_fingerprint=_fp(),
            ))

        # --- income, sized to hit the target savings rate ---
        target_income = total_expense / Decimal(1 - TARGET_SAVINGS_RATE)
        income_rows = []
        # 6 monthly salaries.
        salary_total = Decimal(0)
        for months_ago in range(6):
            when = now - timedelta(days=30 * months_ago + 2)
            amount = Decimal("28000") + Decimal(random.randint(0, 5000))
            salary_total += amount
            income_rows.append(Transaction(
                user=user, description="May Salary" if months_ago == 0 else "Salary",
                amount=amount, direction=Transaction.Direction.IN, category="salary",
                occurred_at=when, source_type=Transaction.SourceType.BANK_SMS,
                source_institution="Equity Bank", reference=_ref(),
                balance_after=Decimal(random.randint(40000, 180000)),
                confidence=0.98, sms_fingerprint=_fp(),
            ))
        # Remaining income spread across many M-Pesa receives. Distribute the
        # required total evenly (with jitter) so the savings rate lands on target.
        n_receive = TARGET_TOTAL - n_expense - len(income_rows) - 1  # -1 for manual juice
        remaining = max(Decimal(0), target_income - salary_total)
        base = remaining / n_receive if n_receive else Decimal(0)
        senders = []
        for name, cat, rng, weight in self.INCOME_SENDERS:
            senders += [(name, cat, rng)] * weight
        for i in range(n_receive):
            name, cat, _ = random.choice(senders)
            if i == n_receive - 1:
                amount = max(Decimal(50), remaining)  # last row absorbs the remainder
            else:
                amount = (base * Decimal(str(random.uniform(0.4, 1.6)))).quantize(Decimal("1"))
                amount = max(Decimal(50), min(amount, remaining - Decimal(50)))
            remaining -= amount
            # Skew receives toward recent months -> gently improving trend.
            days_ago = int(178 * (random.random() ** 1.6))
            when = now - timedelta(days=days_ago,
                                   hours=random.randint(0, 23), minutes=random.randint(0, 59))
            is_mpesa = random.random() < 0.8
            income_rows.append(Transaction(
                user=user, description=name, amount=amount,
                direction=Transaction.Direction.IN, category=cat, occurred_at=when,
                source_type=Transaction.SourceType.MPESA_SMS if is_mpesa else Transaction.SourceType.BANK_SMS,
                source_institution="M-Pesa" if is_mpesa else "KCB Bank",
                reference=_ref(), balance_after=Decimal(random.randint(5000, 120000)),
                confidence=round(random.uniform(0.94, 0.99), 2), sms_fingerprint=_fp(),
            ))

        # one manual + chat-logged style txn for source-badge variety
        manual = Transaction(
            user=user, description="Juice", amount=Decimal("200"),
            direction=Transaction.Direction.OUT, category="food", occurred_at=now,
            source_type=Transaction.SourceType.MANUAL,
        )
        Transaction.objects.bulk_create(expense_rows + income_rows + [manual])
        return Transaction.objects.filter(user=user).count()

    def _seed_budgets(self, user):
        Budget.objects.bulk_create([
            Budget(user=user, name="Groceries", category="food", monthly_limit=Decimal("18500")),
            Budget(user=user, name="Transport", category="transport", monthly_limit=Decimal("6000")),
            Budget(user=user, name="Airtime & Data", category="utilities", monthly_limit=Decimal("2500")),
        ])

    def _seed_goals(self, user, now):
        Goal.objects.bulk_create([
            Goal(user=user, title="Emergency Fund", goal_type=Goal.GoalType.EMERGENCY,
                 target_amount=Decimal("50000"), saved_amount=Decimal("32000"),
                 target_date=(now + timedelta(days=120)).date(), priority=Goal.Priority.HIGH),
            Goal(user=user, title="Laptop Upgrade", goal_type=Goal.GoalType.ELECTRONICS,
                 target_amount=Decimal("95000"), saved_amount=Decimal("58000"),
                 target_date=(now + timedelta(days=150)).date(), priority=Goal.Priority.MEDIUM),
            Goal(user=user, title="Mombasa Trip", goal_type=Goal.GoalType.TRAVEL,
                 target_amount=Decimal("30000"), saved_amount=Decimal("8000"),
                 target_date=(now + timedelta(days=60)).date(), priority=Goal.Priority.LOW),
        ])

    def _seed_chat(self, user):
        ChatMessage.objects.bulk_create([
            ChatMessage(user=user, role="user", content="I'm jobless. How long can my money last?"),
            ChatMessage(user=user, role="assistant",
                        content="With KES 27,500 from May salary and ~KES 4,000/month, your money lasts 6-7 months if you stick to baseline."),
            ChatMessage(user=user, role="user", content="I bought data for 80 ksh today and juice for 200"),
            ChatMessage(user=user, role="assistant",
                        content="Logged both! KES 80 → Utilities (Safaricom data)\nKES 200 → Food & Dining (juice)\nToday total: KES 280"),
        ])

    def _seed_notifications(self, user):
        Notification.objects.bulk_create([
            Notification(user=user, kind="credit", title="50 credits granted",
                         body="Your monthly credits have been refreshed."),
            Notification(user=user, kind="billing", title="Plus trial ending soon",
                         body="Upgrade to keep auto-sync and WhatsApp bot."),
        ])


def _ref() -> str:
    import string
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))


def _fp() -> str:
    import string
    return "".join(random.choices("0123456789abcdef", k=16))
