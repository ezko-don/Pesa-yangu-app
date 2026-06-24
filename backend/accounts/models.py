from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Pesa Yangu user. Email is the primary login identifier."""

    class AccountType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        BUSINESS = "business", "Business"

    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    # Phone & tax id are encrypted at rest in production; stored plainly in dev.
    phone = models.CharField(max_length=20, blank=True)
    tax_id = models.CharField(max_length=20, blank=True)
    account_type = models.CharField(
        max_length=12, choices=AccountType.choices, default=AccountType.INDIVIDUAL
    )
    country = models.CharField(max_length=2, default="KE")
    currency = models.CharField(max_length=3, default="KES")
    two_factor_enabled = models.BooleanField(default=False)
    biometric_enabled = models.BooleanField(default=False)
    whatsapp_connected = models.BooleanField(default=False)
    telegram_connected = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        return self.email or self.username


class SmsSource(models.Model):
    """A connected SMS institution (M-Pesa, Equity, KCB, ...)."""

    class Status(models.TextChoices):
        CONNECTED = "connected", "Connected"
        NOT_CONNECTED = "not_connected", "Not connected"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sms_sources")
    name = models.CharField(max_length=40)  # "M-Pesa", "Equity Bank", ...
    short_code = models.CharField(max_length=6, blank=True)  # "MP", "EQ", "KCB"
    enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CONNECTED)
    transaction_count = models.PositiveIntegerField(default=0)
    last_sync_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.name} ({self.user})"
