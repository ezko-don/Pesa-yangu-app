from django.conf import settings
from django.db import models

# Categories used by the SMS engine + manual entry (spec 3.12).
CATEGORY_CHOICES = [
    ("food", "Food & Dining"),
    ("transport", "Transport"),
    ("utilities", "Utilities"),
    ("shopping", "Shopping"),
    ("entertainment", "Entertainment"),
    ("health", "Health"),
    ("education", "Education"),
    ("salary", "Salary"),
    ("business", "Business Income"),
    ("transfer", "Transfer"),
    ("other", "Other"),
]


class Transaction(models.Model):
    class Direction(models.TextChoices):
        IN = "in", "Income"
        OUT = "out", "Expense"

    class SourceType(models.TextChoices):
        MPESA_SMS = "mpesa_sms", "M-Pesa SMS"
        BANK_SMS = "bank_sms", "Bank SMS"
        MANUAL = "manual", "Manual"
        RECEIPT = "receipt", "Receipt Scan"
        CHAT = "chat", "Hela AI"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions"
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    direction = models.CharField(max_length=3, choices=Direction.choices)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    occurred_at = models.DateTimeField()

    # Provenance — drives the SMS source badges in the UI.
    source_type = models.CharField(
        max_length=12, choices=SourceType.choices, default=SourceType.MANUAL
    )
    source_institution = models.CharField(max_length=40, blank=True)  # "M-Pesa", "Equity Bank"
    reference = models.CharField(max_length=40, blank=True)
    balance_after = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    confidence = models.FloatField(null=True, blank=True)
    # Dedup fingerprint of the originating SMS (never the raw text itself).
    sms_fingerprint = models.CharField(max_length=32, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "sms_fingerprint"],
                condition=~models.Q(sms_fingerprint=""),
                name="unique_user_sms_fingerprint",
            )
        ]

    @property
    def signed_amount(self):
        return self.amount if self.direction == self.Direction.IN else -self.amount

    @property
    def is_auto_synced(self) -> bool:
        return self.source_type in {self.SourceType.MPESA_SMS, self.SourceType.BANK_SMS}

    def __str__(self) -> str:
        return f"{self.description} {self.signed_amount}"


class Budget(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets"
    )
    name = models.CharField(max_length=80)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.name}: {self.monthly_limit}"


class Goal(models.Model):
    class GoalType(models.TextChoices):
        GENERAL = "general", "General savings"
        EMERGENCY = "emergency", "Emergency fund"
        TRAVEL = "travel", "Travel"
        BUSINESS = "business", "Business"
        EDUCATION = "education", "Education"
        ELECTRONICS = "electronics", "Electronics"
        PROPERTY = "property", "Property"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals"
    )
    title = models.CharField(max_length=120)
    goal_type = models.CharField(
        max_length=12, choices=GoalType.choices, default=GoalType.GENERAL
    )
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    saved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField(null=True, blank=True)
    priority = models.CharField(
        max_length=6, choices=Priority.choices, default=Priority.MEDIUM
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    @property
    def is_completed(self) -> bool:
        return self.saved_amount >= self.target_amount

    @property
    def progress_pct(self) -> float:
        if self.target_amount <= 0:
            return 0.0
        return min(100.0, float(self.saved_amount / self.target_amount * 100))

    def __str__(self) -> str:
        return self.title
