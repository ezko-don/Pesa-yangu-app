"""Amount, date and merchant-name normalisation helpers."""
from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Optional

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Tokens stripped from merchant names during normalisation.
_NOISE_SUFFIXES = {
    "LTD", "LIMITED", "LTD.", "CO", "CO.", "COMPANY", "ENTERPRISES", "ENT",
}


def parse_amount(text: str) -> Decimal:
    """'Ksh2,340' / 'KES 5,000.00' / '100.00' -> Decimal."""
    cleaned = re.sub(r"(?i)(ksh|kes)\.?\s*", "", text).replace(",", "").strip()
    return Decimal(cleaned)


def parse_date(text: str, time_text: Optional[str] = None) -> datetime:
    """Parse the date/time formats seen across M-Pesa and bank SMS.

    Supported: d/m/yy, dd/mm/yyyy, dd-Mon-yyyy. Optional 12h time '8:23 AM'.
    """
    text = text.strip()
    dt: Optional[datetime] = None

    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$", text)
    if m:
        d, mo, y = (int(g) for g in m.groups())
        if y < 100:
            y += 2000
        dt = datetime(y, mo, d)
    else:
        m = re.match(r"^(\d{1,2})[- ]([A-Za-z]{3,4})[- ](\d{4})$", text)
        if m:
            d = int(m.group(1))
            mo = _MONTHS[m.group(2).lower()]
            y = int(m.group(3))
            dt = datetime(y, mo, d)

    if dt is None:
        raise ValueError(f"Unrecognised date format: {text!r}")

    if time_text:
        tm = re.match(r"^(\d{1,2}):(\d{2})\s*([AaPp][Mm])?$", time_text.strip())
        if tm:
            hour = int(tm.group(1))
            minute = int(tm.group(2))
            ampm = (tm.group(3) or "").lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            dt = dt.replace(hour=hour, minute=minute)

    return dt


def normalise_merchant(name: Optional[str]) -> Optional[str]:
    """'NAIVAS SUPERMARKET 456789' -> 'Naivas Supermarket'.

    Strips trailing store/account digits and noise corporate suffixes, then
    title-cases the result.
    """
    if not name:
        return None
    name = name.strip()
    # Drop trailing numeric store/account identifiers.
    name = re.sub(r"\s+\d+$", "", name).strip()
    tokens = [t for t in name.split() if t]
    while tokens and tokens[-1].upper().strip(".") in _NOISE_SUFFIXES:
        tokens.pop()
    if not tokens:
        return None
    return " ".join(t.capitalize() for t in tokens)
