"""Structured representation of a parsed financial SMS.

Only these structured fields ever leave the device — never the raw SMS text.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

Direction = str  # "in" | "out"


@dataclass
class ParsedTransaction:
    source: str  # institution, e.g. "M-Pesa", "Equity Bank"
    direction: Direction  # "in" or "out"
    amount: Decimal
    date: datetime
    txn_type: str  # send_money | receive | buy_goods | pay_bill | airtime | withdraw | debit | credit | transfer
    counterparty: Optional[str] = None  # merchant or sender, normalised
    balance: Optional[Decimal] = None
    reference: Optional[str] = None
    account: Optional[str] = None  # masked a/c or paybill/account number
    confidence: float = 1.0
    raw_fingerprint: str = field(default="", repr=False)  # hash of raw text, not the text itself

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "direction": self.direction,
            "amount": str(self.amount),
            "date": self.date.isoformat(),
            "txn_type": self.txn_type,
            "counterparty": self.counterparty,
            "balance": str(self.balance) if self.balance is not None else None,
            "reference": self.reference,
            "account": self.account,
            "confidence": self.confidence,
        }
