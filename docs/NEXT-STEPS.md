# NEXT STEPS — start here next session

> If you are an AI agent or the owner opening this project again: read AGENTS.md first, then this file.

## Current state (short)

**Phase 1 COMPLETE + AI live + Phase 2 #1–#4 (intraday/replay, screener 2.0, journal AI review, alerts) DONE.** 161 tests green, live verified.
- **M1–M6** scaffold, contracts, 3 data adapters, backtest engine, data+backtest API.
- **M7** paper trading (`/api/paper/*`), **M8** strategy storage+sandbox, **M10** AI assistant, **M9** Next.js PWA frontend.
- **Wrap** auth+billing (free/pro, pro gates on strategy save + AI chat), screener (`/api/screener/scan`), journal (`/api/journal/*`), data export (CSV + `scripts/export_to_git.py`), deploy config (compose + nginx + standalone frontend Dockerfile).
- **AI LIVE** — real Gemini key wired (`settings.gemini_api_key`, model `gemini-flash-latest`); live Hinglish replies verified.
- **Intraday + replay** — 1m/1h bars w/ timestamps + interval-scaled defaults; `POST /api/paper/replay`; Dashboard interval picker + Replay-to-Paper button; pct-sizing floor-to-1 fix.
- **Screener 2.0** — RSI/Bollinger %B/vol-ratio/SMA20/MACD indicators + filters + sort; saved scans per user (save/list/delete/run, login-gated).
- **Journal AI review** — `AIAssistant.review_journal()` + `POST /api/journal/review` (Pro); Journal tab "AI Review my Journal" button; live Gemini feedback verified on real entries.
- **Alerts** — `modules/alerts/`: PRICE + RSI(14) one-shot rules, in-app notifications, `/api/alerts/*` (login), background loop behind `ALERTS_ENABLED`; Alerts tab. Live verified (AAPL price rule fired on real quote).

## Next task: Phase 2 (run in this order)

### Phase 2 — Speed (see ROADMAP.md)
- [x] **Intraday + replay** — 1m/1h bars, minute backtest + paper replay (DONE 2026-08-07)
- [x] **Screener 2.0** — indicators (RSI/BB/vol-ratio/MACD/SMA20) + saved scans (DONE 2026-08-07); watchlists + fundamentals still later (no free fundamental data)
- [x] **Journal AI review** — Gemini reads journal entries → patterns + feedback (DONE 2026-08-07; paper-only, Pro-gated)
- [x] **Alerts** — price + RSI one-shot rules, in-app notifications, `/api/alerts/*`, background loop behind `ALERTS_ENABLED` (DONE 2026-08-07)
- [ ] **No-code strategy builder** — visual blocks → generated `signals` code (reuse sandbox)
- [ ] **Education** — in-app lessons, Hinglish/Hindi toggle
- [ ] **Tauri desktop** wrapper + Windows notifications

### Phase 1 leftovers (do before/while Phase 2)
- [ ] Real VPS deploy: `docker compose up --build` (Docker not installed on dev machine — config written, verify on server), domain + HTTPS, prod `NEXT_PUBLIC_API_URL`
- [ ] Data backfill once (NSE ~1 req/day — slow; US/crypto fast), check store size
- [ ] Seed a demo Pro account for the first customer
- [ ] Postgres adoption for users/strategies (currently JSON-file stores — fine for MVP, switch when multi-user)

> Full Phase 2/3 scope — see docs/PLAN.md and docs/ROADMAP.md.

## Rules to remember every session

- **Update AGENTS.md + PROGRESS.md + NEXT-STEPS.md at end of session.**
- **Module isolation is the owner's #1 rule:** changes live inside one module; run that module's tests; never let one feature break another.
- Explain things to the owner in simple Hinglish; keep repo docs in English.
- No code comments unless asked. Commit after meaningful milestones only.
