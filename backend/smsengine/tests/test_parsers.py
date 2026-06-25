"""Parser tests using the exact sample SMS from the Product Spec appendix (11)."""
from datetime import datetime
from decimal import Decimal

import pytest

from smsengine.parsers import parse, parse_many

# (raw, expected_dict) — values taken verbatim from spec appendix 11.1 / 11.2
MPESA_CASES = [
    (
        "TKA2B3CD45 Confirmed. Ksh2,340 sent to NAIVAS SUPERMARKET 456789 on 7/6/26 "
        "at 8:23 AM. New M-PESA balance is Ksh12,450",
        dict(source="M-Pesa", direction="out", amount=Decimal("2340"),
             counterparty="Naivas Supermarket", txn_type="send_money",
             balance=Decimal("12450"), reference="TKA2B3CD45",
             date=datetime(2026, 6, 7, 8, 23)),
    ),
    (
        "BCD987654 Confirmed. You have received Ksh25,000 from CATATU LOGISTICS on "
        "7/6/26. New M-PESA balance is Ksh37,450",
        dict(source="M-Pesa", direction="in", amount=Decimal("25000"),
             counterparty="Catatu Logistics", txn_type="receive",
             balance=Decimal("37450"), date=datetime(2026, 6, 7)),
    ),
    (
        "XYZ123456 Confirmed. Ksh450 paid to JAVA HOUSE KENYA for account 123456 on "
        "7/6/26. New M-PESA balance is Ksh11,950",
        dict(source="M-Pesa", direction="out", amount=Decimal("450"),
             counterparty="Java House Kenya", txn_type="buy_goods",
             balance=Decimal("11950"), date=datetime(2026, 6, 7)),
    ),
    (
        "ABC456789 Confirmed. Ksh1,800 sent to KENYA POWER for account 98765432 on "
        "5/6/26. New M-PESA balance is Ksh14,200",
        dict(source="M-Pesa", direction="out", amount=Decimal("1800"),
             counterparty="Kenya Power", txn_type="pay_bill",
             balance=Decimal("14200"), date=datetime(2026, 6, 5)),
    ),
    (
        "You have bought Ksh100.00 of airtime on 7/6/26 at 9:00 AM. New M-PESA "
        "balance is Ksh13,950",
        dict(source="M-Pesa", direction="out", amount=Decimal("100.00"),
             counterparty="Safaricom Airtime", txn_type="airtime",
             balance=Decimal("13950"), date=datetime(2026, 6, 7, 9, 0)),
    ),
]

BANK_CASES = [
    (
        "Equity Bank: Ksh1,800 debited from a/c ****1234 on 05-Jun-2026. "
        "Narration: KENYA POWER. Available balance: Ksh24,200",
        dict(source="Equity Bank", direction="out", amount=Decimal("1800"),
             counterparty="Kenya Power", balance=Decimal("24200"),
             date=datetime(2026, 6, 5), account="****1234"),
    ),
    (
        "KCB: Your a/c ****5678 debited KES 5,000.00 on 06/06/2026. Ref: TRANSFER. "
        "Avail bal: KES 18,450.00",
        dict(source="KCB Bank", direction="out", amount=Decimal("5000.00"),
             txn_type="transfer", balance=Decimal("18450.00"),
             date=datetime(2026, 6, 6), account="****5678"),
    ),
    (
        "Co-opBank: KES 12,000 credited to a/c ****9012 on 07-Jun-2026. "
        "Narration: SALARY. Bal: KES 30,450",
        dict(source="Co-op Bank", direction="in", amount=Decimal("12000"),
             counterparty="Salary", balance=Decimal("30450"),
             date=datetime(2026, 6, 7), account="****9012"),
    ),
]


@pytest.mark.parametrize("raw,expected", MPESA_CASES + BANK_CASES)
def test_parse_matches_spec_fixtures(raw, expected):
    txn = parse(raw)
    assert txn is not None, f"failed to parse: {raw!r}"
    for key, want in expected.items():
        assert getattr(txn, key) == want, f"{key}: got {getattr(txn, key)!r}, want {want!r}"
    assert txn.confidence >= 0.9


def test_airtel_money_send_and_receive():
    recv = parse("You have received Ksh500 from JOHN DOE. Your Airtel Money balance is Ksh1,200.")
    assert recv is not None and recv.direction == "in" and recv.amount == Decimal("500")
    sent = parse("You have sent Ksh300 to JANE DOE. Your Airtel Money balance is Ksh900.")
    assert sent is not None and sent.direction == "out" and sent.amount == Decimal("300")


def test_unrecognised_returns_none():
    assert parse("Your OTP is 123456. Do not share it with anyone.") is None
    assert parse("") is None


def test_parse_many_drops_unrecognised():
    msgs = [
        "TKA2B3CD45 Confirmed. Ksh2,340 sent to NAIVAS SUPERMARKET 456789 on 7/6/26 "
        "at 8:23 AM. New M-PESA balance is Ksh12,450",
        "Your OTP is 999999.",
        "Co-opBank: KES 12,000 credited to a/c ****9012 on 07-Jun-2026. "
        "Narration: SALARY. Bal: KES 30,450",
    ]
    out = parse_many(msgs)
    assert len(out) == 2
    assert out[0].source == "M-Pesa"
    assert out[1].source == "Co-op Bank"


def test_send_vs_paybill_disambiguation():
    # paybill has "for account"; plain send does not
    paybill = parse("ABC456789 Confirmed. Ksh1,800 sent to KENYA POWER for account 98765432 "
                    "on 5/6/26. New M-PESA balance is Ksh14,200")
    send = parse("TKA2B3CD45 Confirmed. Ksh2,340 sent to NAIVAS SUPERMARKET 456789 on 7/6/26 "
                 "at 8:23 AM. New M-PESA balance is Ksh12,450")
    assert paybill.txn_type == "pay_bill"
    assert send.txn_type == "send_money"
