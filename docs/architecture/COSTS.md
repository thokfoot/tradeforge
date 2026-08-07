# Cost Model / Budget (owner: very little money, lots of time)

## Monthly cost by phase (target)

| Item | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|
| Server (VPS) | ₹0 (Oracle free) → ₹500 (Hetzner) | ~₹1,500 | ~₹3,000 |
| Market data | ₹0 (free sources) | ₹0–500 (US intraday cheap) | ₹1,000–3,000 (India intraday + options) |
| AI | ₹0 (Gemini Flash free tier) | ₹0–500 | ₹1,000+ (as users grow) |
| Tools/DB (open source) | ₹0 | ₹0 | ₹0 |
| Domain | ₹800/yr (optional; free subdomain first) | — | — |
| **Total** | **₹0–500/mo** | **~₹2,000/mo** | **~₹5,000/mo** |

One-time: India intraday bulk archive **~₹5,000–15,000** (Phase 3) — one-time preferred over monthly subscription.

## Revenue model (simple math)

- Freemium: Free tier (charts, watchlists, basic paper trading, limited backtests/day) for acquisition.
- Pro: ₹99–199/mo target (all features, all markets).
- Expert tier: ₹299–499/mo later (options, API, advanced analytics).
- **Break-even:**
  - 10 customers × ₹199 = ₹1,990/mo → covers Phase 2 (server + data)
  - 25 customers × ₹199 = ₹4,975/mo → covers Phase 3
  - 100 customers → profit, funds paid data + better AI

## AI cost reality (why free tier first)
- Gemini Flash free tier: generous daily limits — fine for 100–200 active users chatting.
- After that: ~₹1–3 per customer/month. Charge a small "AI features" premium (e.g., +₹50/mo) later to cover it.
- Jio free Gemini Pro = personal use only, NOT an API (no programmatic access).

## What stays ₹0 (locked choices)
- PWA (installable mobile + Windows) — no app-store fees (saves ₹3,500 Play + ₹6,700/yr Apple + 30% cut)
- Open-source stack: FastAPI, Postgres, Redis, Parquet, Docker, lightweight-charts, React
- SSL via Let's Encrypt
- Backups: object storage on the same/cheap bucket

## Rules
- No paid service before Phase 3 unless revenue exists.
- Re-verify prices (server, data, AI) each phase — 2026 prices move.
