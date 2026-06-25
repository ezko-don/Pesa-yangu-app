"""Institution-specific SMS parsers.

Each parser is a list of (compiled regex, builder) rules. Builders receive the
regex match plus the raw text and return a ParsedTransaction. The public
``parse`` function tries every institution and returns the highest-confidence
result, or ``None`` if nothing matches.

Adding support for a new bank = adding a new InstitutionParser. Patterns are
versioned here so a Safaricom/bank format change is a localised edit.
"""
from __future__ import annotations

import hashlib
import re
from typing import Callable, List, Optional, Tuple

from .models import ParsedTransaction
from .normalise import normalise_merchant, parse_amount, parse_date

# Reusable fragments
_AMT = r"(?:Ksh|KES)\.?\s?[\d,]+(?:\.\d{2})?"
_DATE = r"\d{1,2}[/-](?:\d{1,2}|[A-Za-z]{3,4})[/-]\d{2,4}"
_TIME = r"\d{1,2}:\d{2}\s?[AaPp][Mm]"

Builder = Callable[[re.Match, str], ParsedTransaction]
Rule = Tuple[re.Pattern, Builder]


def _fp(raw: str) -> str:
    return hashlib.sha256(raw.strip().encode()).hexdigest()[:16]


class InstitutionParser:
    name: str
    rules: List[Rule]

    def parse(self, raw: str) -> Optional[ParsedTransaction]:
        for pattern, build in self.rules:
            m = pattern.search(raw)
            if m:
                txn = build(m, raw)
                txn.raw_fingerprint = _fp(raw)
                return txn
        return None


# --------------------------------------------------------------------------- #
# M-Pesa (Safaricom)
# --------------------------------------------------------------------------- #
class MpesaParser(InstitutionParser):
    name = "M-Pesa"

    def __init__(self) -> None:
        self.rules = [
            # Pay bill: "... Ksh1,800 sent to KENYA POWER for account 98765432 on 5/6/26 ..."
            (
                re.compile(
                    rf"^(?P<ref>[A-Z0-9]+) Confirmed\.\s*(?P<amt>{_AMT}) sent to "
                    rf"(?P<name>.+?) for account (?P<acct>\w+) on (?P<date>{_DATE})"
                    rf"(?: at (?P<time>{_TIME}))?\..*?balance is (?P<bal>{_AMT})",
                    re.IGNORECASE,
                ),
                lambda m, raw: self._build(m, raw, "out", "pay_bill"),
            ),
            # Buy goods (Till): "... Ksh450 paid to JAVA HOUSE KENYA for account 123456 on ..."
            (
                re.compile(
                    rf"^(?P<ref>[A-Z0-9]+) Confirmed\.\s*(?P<amt>{_AMT}) paid to "
                    rf"(?P<name>.+?) for account (?P<acct>\w+) on (?P<date>{_DATE})"
                    rf"(?: at (?P<time>{_TIME}))?\..*?balance is (?P<bal>{_AMT})",
                    re.IGNORECASE,
                ),
                lambda m, raw: self._build(m, raw, "out", "buy_goods"),
            ),
            # Send money: "... Ksh2,340 sent to NAIVAS SUPERMARKET 456789 on 7/6/26 at 8:23 AM ..."
            (
                re.compile(
                    rf"^(?P<ref>[A-Z0-9]+) Confirmed\.\s*(?P<amt>{_AMT}) sent to "
                    rf"(?P<name>.+?) on (?P<date>{_DATE})"
                    rf"(?: at (?P<time>{_TIME}))?\..*?balance is (?P<bal>{_AMT})",
                    re.IGNORECASE,
                ),
                lambda m, raw: self._build(m, raw, "out", "send_money"),
            ),
            # Receive: "... You have received Ksh25,000 from CATATU LOGISTICS on 7/6/26 ..."
            (
                re.compile(
                    rf"^(?P<ref>[A-Z0-9]+) Confirmed\.\s*You have received (?P<amt>{_AMT}) from "
                    rf"(?P<name>.+?) on (?P<date>{_DATE})"
                    rf"(?: at (?P<time>{_TIME}))?\..*?balance is (?P<bal>{_AMT})",
                    re.IGNORECASE,
                ),
                lambda m, raw: self._build(m, raw, "in", "receive"),
            ),
            # Withdraw: "... Withdraw Ksh1,000 from 12345 - AGENT NAME ... balance is ..."
            (
                re.compile(
                    rf"^(?P<ref>[A-Z0-9]+) Confirmed\.\s*(?:on .+? )?Withdraw (?P<amt>{_AMT}) from "
                    rf"(?P<name>.+?) on (?P<date>{_DATE})"
                    rf"(?: at (?P<time>{_TIME}))?\..*?balance is (?P<bal>{_AMT})",
                    re.IGNORECASE,
                ),
                lambda m, raw: self._build(m, raw, "out", "withdraw"),
            ),
            # Airtime: "You have bought Ksh100.00 of airtime on 7/6/26 at 9:00 AM ..."
            (
                re.compile(
                    rf"You have bought (?P<amt>{_AMT}) of airtime on (?P<date>{_DATE})"
                    rf"(?: at (?P<time>{_TIME}))?\..*?balance is (?P<bal>{_AMT})",
                    re.IGNORECASE,
                ),
                lambda m, raw: self._build_airtime(m, raw),
            ),
        ]

    def _build(self, m: re.Match, raw: str, direction: str, txn_type: str) -> ParsedTransaction:
        g = m.groupdict()
        return ParsedTransaction(
            source=self.name,
            direction=direction,
            amount=parse_amount(g["amt"]),
            date=parse_date(g["date"], g.get("time")),
            txn_type=txn_type,
            counterparty=normalise_merchant(g.get("name")),
            balance=parse_amount(g["bal"]) if g.get("bal") else None,
            reference=g.get("ref"),
            account=g.get("acct"),
            confidence=0.98,
        )

    def _build_airtime(self, m: re.Match, raw: str) -> ParsedTransaction:
        g = m.groupdict()
        return ParsedTransaction(
            source=self.name,
            direction="out",
            amount=parse_amount(g["amt"]),
            date=parse_date(g["date"], g.get("time")),
            txn_type="airtime",
            counterparty="Safaricom Airtime",
            balance=parse_amount(g["bal"]) if g.get("bal") else None,
            confidence=0.97,
        )


# --------------------------------------------------------------------------- #
# Banks
# --------------------------------------------------------------------------- #
class EquityParser(InstitutionParser):
    name = "Equity Bank"

    def __init__(self) -> None:
        self.rules = [
            (
                re.compile(
                    rf"Equity Bank:\s*(?P<amt>{_AMT}) (?P<dir>debited|credited)(?: from| to)? "
                    rf"a/c (?P<acct>\*+\d+) on (?P<date>{_DATE})\.\s*"
                    rf"Narration:\s*(?P<name>.+?)\.\s*Available balance:\s*(?P<bal>{_AMT})",
                    re.IGNORECASE,
                ),
                lambda m, raw: _build_bank(self.name, m),
            ),
        ]


class KcbParser(InstitutionParser):
    name = "KCB Bank"

    def __init__(self) -> None:
        self.rules = [
            (
                re.compile(
                    rf"KCB:\s*Your a/c (?P<acct>\*+\d+) (?P<dir>debited|credited)\s*(?P<amt>{_AMT}) "
                    rf"on (?P<date>{_DATE})\.\s*Ref:\s*(?P<name>.+?)\.\s*Avail bal:\s*(?P<bal>{_AMT})",
                    re.IGNORECASE,
                ),
                lambda m, raw: _build_bank(self.name, m, is_ref=True),
            ),
        ]


class CoopParser(InstitutionParser):
    name = "Co-op Bank"

    def __init__(self) -> None:
        self.rules = [
            (
                re.compile(
                    rf"Co-opBank:\s*(?P<amt>{_AMT}) (?P<dir>debited|credited)(?: from| to)? "
                    rf"a/c (?P<acct>\*+\d+) on (?P<date>{_DATE})\.\s*"
                    rf"Narration:\s*(?P<name>.+?)\.\s*Bal:\s*(?P<bal>{_AMT})",
                    re.IGNORECASE,
                ),
                lambda m, raw: _build_bank(self.name, m),
            ),
        ]


class AirtelMoneyParser(InstitutionParser):
    name = "Airtel Money"

    def __init__(self) -> None:
        self.rules = [
            # Receive: "You have received Ksh500 from JOHN DOE. Your Airtel Money balance is Ksh1,200. ..."
            (
                re.compile(
                    rf"You have received (?P<amt>{_AMT}) from (?P<name>.+?)\.\s*"
                    rf"Your Airtel Money balance is (?P<bal>{_AMT})\.?(?:.*?on (?P<date>{_DATE}))?",
                    re.IGNORECASE,
                ),
                lambda m, raw: _build_airtel("in", "receive", m),
            ),
            # Send/pay: "You have sent Ksh500 to JANE DOE. Your Airtel Money balance is Ksh700. ..."
            (
                re.compile(
                    rf"You have (?:sent|paid) (?P<amt>{_AMT}) to (?P<name>.+?)\.\s*"
                    rf"Your Airtel Money balance is (?P<bal>{_AMT})\.?(?:.*?on (?P<date>{_DATE}))?",
                    re.IGNORECASE,
                ),
                lambda m, raw: _build_airtel("out", "send_money", m),
            ),
        ]


def _build_bank(source: str, m: re.Match, is_ref: bool = False) -> ParsedTransaction:
    g = m.groupdict()
    direction = "out" if g["dir"].lower() == "debited" else "in"
    name = g.get("name")
    txn_type = "debit" if direction == "out" else "credit"
    counterparty = normalise_merchant(name)
    # KCB uses a free-form Ref (e.g. TRANSFER); surface it as txn_type when generic.
    if is_ref and name and name.strip().lower() in {"transfer", "withdrawal", "deposit"}:
        txn_type = name.strip().lower()
        counterparty = None
    return ParsedTransaction(
        source=source,
        direction=direction,
        amount=parse_amount(g["amt"]),
        date=parse_date(g["date"]),
        txn_type=txn_type,
        counterparty=counterparty,
        balance=parse_amount(g["bal"]) if g.get("bal") else None,
        account=g.get("acct"),
        confidence=0.97,
    )


def _build_airtel(direction: str, txn_type: str, m: re.Match) -> ParsedTransaction:
    g = m.groupdict()
    from datetime import datetime as _dt
    date = parse_date(g["date"]) if g.get("date") else _dt.now()
    return ParsedTransaction(
        source="Airtel Money",
        direction=direction,
        amount=parse_amount(g["amt"]),
        date=date,
        txn_type=txn_type,
        counterparty=normalise_merchant(g.get("name")),
        balance=parse_amount(g["bal"]) if g.get("bal") else None,
        confidence=0.9 if not g.get("date") else 0.95,
    )


_PARSERS: List[InstitutionParser] = [
    MpesaParser(),
    EquityParser(),
    KcbParser(),
    CoopParser(),
    AirtelMoneyParser(),
]


def parse(raw: str) -> Optional[ParsedTransaction]:
    """Parse a single SMS. Returns the best match, or None if unrecognised."""
    best: Optional[ParsedTransaction] = None
    for p in _PARSERS:
        txn = p.parse(raw)
        if txn and (best is None or txn.confidence > best.confidence):
            best = txn
    return best


def parse_many(messages: List[str]) -> List[ParsedTransaction]:
    """Parse a batch, dropping unrecognised messages. Order preserved."""
    out: List[ParsedTransaction] = []
    for raw in messages:
        txn = parse(raw)
        if txn:
            out.append(txn)
    return out
