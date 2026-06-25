"""SMS sync pipeline: structured fields -> categorised Transactions.

The mobile client parses raw SMS *on device* (raw text never leaves the phone)
and posts only the structured fields here. For dev/testing we also accept raw
SMS and run them through the same engine server-side.
"""
from __future__ import annotations

from typing import List

from django.utils import timezone

from smsengine.models import ParsedTransaction
from smsengine.parsers import parse as parse_sms

from .categorize import categorize_parsed, normalise_description
from .models import Transaction

_SOURCE_TYPE = {
    "M-Pesa": Transaction.SourceType.MPESA_SMS,
}


def _source_type_for(institution: str) -> str:
    return _SOURCE_TYPE.get(institution, Transaction.SourceType.BANK_SMS)


def ingest_parsed(user, parsed: ParsedTransaction) -> Transaction | None:
    """Create a Transaction from a parsed SMS, deduping on fingerprint."""
    if parsed.raw_fingerprint and Transaction.objects.filter(
        user=user, sms_fingerprint=parsed.raw_fingerprint
    ).exists():
        return None
    txn = Transaction.objects.create(
        user=user,
        description=normalise_description(parsed),
        amount=parsed.amount,
        direction=parsed.direction,
        category=categorize_parsed(parsed),
        occurred_at=parsed.date if timezone.is_aware(parsed.date)
        else timezone.make_aware(parsed.date),
        source_type=_source_type_for(parsed.source),
        source_institution=parsed.source,
        reference=parsed.reference or "",
        balance_after=parsed.balance,
        confidence=parsed.confidence,
        sms_fingerprint=parsed.raw_fingerprint,
    )
    return txn


def ingest_raw_messages(user, messages: List[str]) -> dict:
    """Parse + ingest a batch of raw SMS. Returns counts (dev/testing path)."""
    created = 0
    skipped = 0
    unparsed = 0
    for raw in messages:
        parsed = parse_sms(raw)
        if not parsed:
            unparsed += 1
            continue
        txn = ingest_parsed(user, parsed)
        if txn:
            created += 1
        else:
            skipped += 1
    return {"created": created, "skipped_duplicates": skipped, "unparsed": unparsed}
