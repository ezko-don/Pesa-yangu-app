# Pesa Yangu

AI-powered personal finance app for Kenya. Parses transaction SMS on-device into
structured records, scores financial health, and gives in-app guidance through
**Hela**, a money copilot.

## Repository layout

| Path | Description |
|------|-------------|
| `backend/` | Django + DRF API: SMS parsing engine, finance models/analytics, Hela AI, demo seed |
| `mobile/`  | Expo (React Native) app: 5-tab navigation and screens wired to the API |

## Quick start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # demo@pesayangu.co.ke / pesayangu
python manage.py runserver
```

Optional: set `ANTHROPIC_API_KEY` to enable Claude-backed Hela and AI
categorisation. Without it, Hela falls back to a grounded responder over the
user's real numbers.

### Mobile

```bash
cd mobile
npm install
npm start          # then press "w" for web, or scan the QR for a device
```

The API base URL auto-resolves per platform (Android emulator → `10.0.2.2`).

## Privacy

The SMS engine stores **structured fields only** (amount, merchant, direction,
timestamp) and a SHA256 fingerprint for deduplication — never the raw message.

## Status

Phase 1 (MVP): backend + SMS engine + mobile screens on Expo. Live
M-Pesa/OTP/WhatsApp integration is planned for later phases.
