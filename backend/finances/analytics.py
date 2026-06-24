"""Financial-health analytics — health score, signals, trends, breakdowns.

These power the Home Dashboard and Reports screens (spec 3.2 / 3.6).
All functions operate on a queryset of the user's Transactions.
"""
from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, Iterable, List

from .models import CATEGORY_CHOICES, Transaction

_CATEGORY_LABELS = dict(CATEGORY_CHOICES)


def _money(value) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("0.01"))


@dataclass
class Period:
    money_in: Decimal
    money_out: Decimal
    count: int

    @property
    def net(self) -> Decimal:
        return self.money_in - self.money_out


def period_summary(txns: Iterable[Transaction]) -> Period:
    money_in = Decimal(0)
    money_out = Decimal(0)
    count = 0
    for t in txns:
        count += 1
        if t.direction == Transaction.Direction.IN:
            money_in += t.amount
        else:
            money_out += t.amount
    return Period(_money(money_in), _money(money_out), count)


def savings_rate(p: Period) -> float:
    if p.money_in <= 0:
        return 0.0
    return float((p.money_in - p.money_out) / p.money_in * 100)


def spend_pace(p: Period) -> float:
    if p.money_in <= 0:
        return 100.0 if p.money_out > 0 else 0.0
    return float(p.money_out / p.money_in * 100)


def category_breakdown(txns: Iterable[Transaction]) -> List[dict]:
    totals: Dict[str, Decimal] = defaultdict(Decimal)
    grand = Decimal(0)
    for t in txns:
        if t.direction == Transaction.Direction.OUT:
            totals[t.category] += t.amount
            grand += t.amount
    rows = []
    for cat, amount in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
        pct = float(amount / grand * 100) if grand > 0 else 0.0
        rows.append({
            "category": cat,
            "label": _CATEGORY_LABELS.get(cat, cat.title()),
            "amount": str(_money(amount)),
            "pct": round(pct, 1),
        })
    return rows


def spend_concentration(txns: Iterable[Transaction]) -> dict:
    rows = category_breakdown(txns)
    if not rows:
        return {"top_category": None, "top_label": None, "pct": 0.0, "concentrated": False}
    top = rows[0]
    return {
        "top_category": top["category"],
        "top_label": top["label"],
        "pct": top["pct"],
        "concentrated": top["pct"] >= 50.0,
    }


def emergency_runway_months(p: Period, monthly_expenses: Decimal) -> float:
    """Months of average expenses covered by net cash this period."""
    if monthly_expenses <= 0:
        return 0.0
    return round(float(p.net / monthly_expenses), 1) if p.net > 0 else 0.0


def health_score(p: Period, concentration_pct: float, net_trend_positive: bool) -> int:
    """0–100 composite of savings rate, spend pace, net trend, concentration.

    Thresholds reflect real personal-finance guidance: a ~20–30% savings rate is
    already excellent, so the components saturate at realistic, healthy values
    rather than only rewarding extreme behaviour.
    """
    sr = savings_rate(p)
    sp = spend_pace(p)
    # savings rate component (0–40): full marks at a 30% savings rate.
    sr_pts = max(0.0, min(40.0, sr / 30 * 40))
    # spend pace component (0–25): healthy when spending <= 70% of income.
    sp_pts = max(0.0, min(25.0, (100 - sp) / 30 * 25))
    # concentration component (0–20): full marks at <=30% in one category.
    if concentration_pct <= 30:
        conc_pts = 20.0
    else:
        conc_pts = max(0.0, 20.0 * (60 - concentration_pct) / 30)
    # net trend component (0–15)
    trend_pts = 15.0 if net_trend_positive else 0.0
    return int(round(sr_pts + sp_pts + conc_pts + trend_pts))


def monthly_cashflow(txns: Iterable[Transaction], months: int = 6) -> List[dict]:
    """Income vs expense per month for the trailing ``months`` months."""
    buckets: Dict[tuple, Dict[str, Decimal]] = defaultdict(lambda: {"in": Decimal(0), "out": Decimal(0)})
    for t in txns:
        key = (t.occurred_at.year, t.occurred_at.month)
        buckets[key]["in" if t.direction == Transaction.Direction.IN else "out"] += t.amount

    today = date.today()
    series: List[dict] = []
    year, month = today.year, today.month
    keys = []
    for _ in range(months):
        keys.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    for (y, m) in reversed(keys):
        b = buckets.get((y, m), {"in": Decimal(0), "out": Decimal(0)})
        series.append({
            "label": calendar.month_abbr[m],
            "year": y,
            "month": m,
            "income": str(_money(b["in"])),
            "expenses": str(_money(b["out"])),
            "net": str(_money(b["in"] - b["out"])),
        })
    return series


def average_monthly_margin(series: List[dict]) -> str:
    if not series:
        return "0.00"
    total = sum(Decimal(row["net"]) for row in series)
    return str(_money(total / len(series)))


def net_trend_positive(series: List[dict]) -> bool:
    """True when recent months trend above earlier months.

    Compares the average net of the most recent half of the series against the
    earlier half — far more stable than a single month-over-month comparison.
    """
    if len(series) < 2:
        return False
    nets = [Decimal(row["net"]) for row in series]
    half = len(nets) // 2
    earlier = nets[:half]
    recent = nets[half:]
    avg_earlier = sum(earlier) / len(earlier)
    avg_recent = sum(recent) / len(recent)
    return avg_recent >= avg_earlier
