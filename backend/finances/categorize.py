"""Transaction categorisation.

Default is a fast, deterministic keyword classifier (no network, works offline).
When an Anthropic key is configured, ``categorize`` can defer to Claude, but the
keyword classifier is always the fallback so the app works without AI credits.
"""
from __future__ import annotations

from typing import Optional

from smsengine.models import ParsedTransaction

# Ordered keyword -> category map. First hit wins.
_KEYWORDS = [
    ("salary", "salary"),
    ("payroll", "salary"),
    ("naivas", "food"),
    ("carrefour", "food"),
    ("java house", "food"),
    ("kfc", "food"),
    ("restaurant", "food"),
    ("supermarket", "food"),
    ("matatu", "transport"),
    ("bolt", "transport"),
    ("uber", "transport"),
    ("little cab", "transport"),
    ("shell", "transport"),
    ("total", "transport"),
    ("fuel", "transport"),
    ("kenya power", "utilities"),
    ("kplc", "utilities"),
    ("nairobi water", "utilities"),
    ("safaricom", "utilities"),
    ("airtime", "utilities"),
    ("data", "utilities"),
    ("zuku", "utilities"),
    ("dstv", "entertainment"),
    ("netflix", "entertainment"),
    ("showmax", "entertainment"),
    ("hospital", "health"),
    ("pharmacy", "health"),
    ("chemist", "health"),
    ("clinic", "health"),
    ("school", "education"),
    ("university", "education"),
    ("college", "education"),
    ("fees", "education"),
]

# M-Pesa / bank transaction types map directly to categories.
_TYPE_MAP = {
    "airtime": "utilities",
    "transfer": "transfer",
    "withdraw": "transfer",
}


def categorize_text(description: str, direction: str) -> str:
    text = (description or "").lower()
    for kw, cat in _KEYWORDS:
        if kw in text:
            return cat
    if direction == "in":
        return "salary" if "salary" in text else "business"
    return "other"


def categorize_parsed(txn: ParsedTransaction) -> str:
    """Categorise a parsed SMS transaction (used by the sync pipeline)."""
    if txn.txn_type in _TYPE_MAP:
        return _TYPE_MAP[txn.txn_type]
    if txn.txn_type in {"receive", "credit"}:
        name = (txn.counterparty or "").lower()
        if "salary" in name or txn.txn_type == "credit" and "salary" in name:
            return "salary"
    return categorize_text(txn.counterparty or "", txn.direction)


def normalise_description(txn: ParsedTransaction) -> str:
    if txn.txn_type == "airtime":
        return "Airtime"
    if txn.counterparty:
        return txn.counterparty
    return txn.txn_type.replace("_", " ").title()
