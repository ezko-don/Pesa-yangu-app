"""Hela AI — the in-app financial advisor.

Uses Anthropic Claude when ANTHROPIC_API_KEY is configured; otherwise falls back
to a deterministic, data-grounded responder so the app is fully demoable without
AI credits. Both paths receive the user's financial context.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from django.conf import settings

from finances import analytics
from finances.categorize import categorize_text
from finances.models import Transaction

SYSTEM_PROMPT = (
    "You are Hela, a friendly Kenyan personal-finance advisor inside the Pesa Yangu app. "
    "You have access to the user's full transaction history. Be concise, practical and warm. "
    "Use KES amounts. You may answer in English or Swahili if the user does."
)


def build_context(user) -> dict:
    txns = list(Transaction.objects.filter(user=user))
    p = analytics.period_summary(txns)
    concentration = analytics.spend_concentration(txns)
    return {
        "transaction_count": p.count,
        "money_in": str(p.money_in),
        "money_out": str(p.money_out),
        "net": str(p.net),
        "savings_rate": round(analytics.savings_rate(p), 1),
        "top_category": concentration.get("top_label"),
        "top_category_pct": concentration.get("pct"),
    }


def _detect_logged_transaction(message: str) -> Optional[dict]:
    """Parse a natural-language log like 'data 80 and juice 200'."""
    import re

    items = []
    # pattern: <words> <amount>  e.g. "data 80", "juice 200"
    for m in re.finditer(r"([A-Za-z][A-Za-z ]*?)\s+(\d+(?:\.\d{1,2})?)", message):
        label = m.group(1).strip()
        amount = Decimal(m.group(2))
        if label and amount > 0:
            items.append({
                "description": label.title(),
                "amount": amount,
                "category": categorize_text(label, "out"),
            })
    return {"items": items} if items else None


def respond(user, message: str, history: Optional[List[dict]] = None) -> dict:
    """Return {'reply': str, 'logged': [...]}.

    If Claude is configured it is used; otherwise a grounded fallback runs.
    """
    ctx = build_context(user)
    logged = _maybe_log(user, message)

    if settings.ANTHROPIC_API_KEY:
        reply = _claude_reply(message, ctx, history or [])
    else:
        reply = _fallback_reply(message, ctx, logged)
    return {"reply": reply, "logged": logged}


def _maybe_log(user, message: str) -> List[dict]:
    parsed = _detect_logged_transaction(message)
    created = []
    if not parsed:
        return created
    from django.utils import timezone

    # Only treat as a log if the message reads like one (has a verb cue or is terse).
    cue = any(w in message.lower() for w in ["spent", "bought", "paid", "log", "add"])
    terse = len(message.split()) <= 8
    if not (cue or terse):
        return created
    for item in parsed["items"]:
        txn = Transaction.objects.create(
            user=user,
            description=item["description"],
            amount=item["amount"],
            direction=Transaction.Direction.OUT,
            category=item["category"],
            occurred_at=timezone.now(),
            source_type=Transaction.SourceType.CHAT,
        )
        created.append({
            "id": txn.id, "description": txn.description,
            "amount": str(txn.amount), "category": txn.get_category_display(),
        })
    return created


def _fallback_reply(message: str, ctx: dict, logged: List[dict]) -> str:
    if logged:
        lines = ["Logged! 🎉"]
        total = sum(Decimal(i["amount"]) for i in logged)
        for i in logged:
            lines.append(f"KES {i['amount']} → {i['category']}")
        lines.append(f"Today total: KES {total}")
        return "\n".join(lines)

    msg = message.lower()
    if "food" in msg:
        return (f"Food & Dining is your top category at {ctx['top_category_pct']}% of spending. "
                f"That's high — trimming it is the fastest win.")
    if "save" in msg or "saving" in msg:
        return (f"Your savings rate is {ctx['savings_rate']}%. "
                f"You've kept KES {ctx['net']} of KES {ctx['money_in']} earned this period.")
    if "afford" in msg or "last" in msg or "jobless" in msg:
        return (f"With net KES {ctx['net']} and your current spend, you have a healthy buffer. "
                f"Build an emergency fund of 3–6 months of expenses first.")
    if "tax" in msg or "kra" in msg:
        return "Next KRA deadline is 30 Jun 2026. Set up your Tax Profile and I'll pre-fill PAYE from your income."
    return (f"Habari! I've analysed your {ctx['transaction_count']} transactions. "
            f"Money in KES {ctx['money_in']}, out KES {ctx['money_out']}, "
            f"savings rate {ctx['savings_rate']}%. Ask me anything about your money.")


def _claude_reply(message: str, ctx: dict, history: List[dict]) -> str:
    try:
        import anthropic
    except ImportError:
        return _fallback_reply(message, ctx, [])
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    messages = [{"role": h["role"], "content": h["content"]} for h in history]
    messages.append({
        "role": "user",
        "content": f"My financial context: {ctx}\n\nQuestion: {message}",
    })
    resp = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return "".join(block.text for block in resp.content if block.type == "text")
