---
name: testing-pesa-yangu
description: End-to-end test the Pesa Yangu MVP (Django API + Expo web mobile app) on Expo web. Use when verifying login/dashboard, transactions, Hela AI, or read screens after backend or mobile changes.
---

# Testing Pesa Yangu (Phase 1 MVP)

Personal-finance app: Django REST backend (`backend/`) + Expo React Native app (`mobile/`). Test on Expo web.

## Start the environment
Processes do NOT persist across VM restarts — re-start both servers first.

```bash
# Backend (terminal 1)
cd backend && source .venv/bin/activate   # venv may be at backend/.venv
python manage.py migrate                  # SQLite; data persists on disk
python manage.py seed_demo                # idempotent; creates demo account + 847 txns
python manage.py runserver 0.0.0.0:8000

# Mobile web (terminal 2)
cd mobile && npx expo start --web --port 8081
```

- App: http://localhost:8081  ·  API: http://localhost:8000/api/
- Demo account: `demo@pesayangu.co.ke` / `pesayangu` (847 txns, health score 88).

## Gotchas
- **Stale auth:** JWT persists in AsyncStorage across restarts, so the app may open straight to the dashboard. For a clean login test, go to More → Log out first, then test the login flow.
- **Hela AI:** With no `ANTHROPIC_API_KEY` set, Hela runs in grounded fallback mode — replies are still non-empty and reference the user's real numbers (e.g. top spending category). That is expected, not a bug.
- **SMS / M-Pesa / OTP / WhatsApp:** interface-stubbed in the MVP (need a physical device + credentials). Don't try to test live ingestion; the parser is covered by backend unit tests (`backend/smsengine/tests/`).
- Login screen browser tab title may show "undefined" — cosmetic, not a failure.

## Test plan (golden path)
Concrete plan with exact expected values lives at `TEST_PLAN.md` in repo root. Summary:
1. **T1 Login + Dashboard** — demo login → Home; Health **88**, Net **+KES 68K**, Savings **24.9%**, Spend **75.1%**, auto-sync banner.
2. **T2 Money** — Money In **271,249** / Out **~203,637**; list renders; search filters; adding a txn persists (count increments, new row at top).
3. **T3 Hela AI** — send a message → user bubble + grounded assistant reply.
4. **T4 Goals / Reports / Connected Accounts** — Goals ≥3 cards w/ progress; Reports 6-month chart + categories; Connected Accounts M-Pesa **847**.

## Evidence
- Record the walkthrough; annotate with `annotate_recording` (setup / test_start / assertion).
- Capture a screenshot per screen. Post ONE PR comment with results + session link; embed video as animated webp (mp4 can't embed in PR comments):
  `ffmpeg -y -i edited.mp4 -vf "fps=8,scale=900:-1:flags=lanczos" -loop 0 out.webp`

## Devin Secrets Needed
- None required for the golden-path test (grounded fallback works offline).
- Optional: `ANTHROPIC_API_KEY` to exercise live Hela AI / AI categorization.
