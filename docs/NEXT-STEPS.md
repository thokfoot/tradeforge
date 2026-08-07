# NEXT STEPS — start here next session

> If you are an AI agent or the owner opening this project again: read AGENTS.md first, then this file.

## Current state (short)

**Phase 1 COMPLETE.** All milestones + wrap shipped, 124 tests green, live verified.
- **M1–M6** scaffold, contracts, 3 data adapters, backtest engine, data+backtest API.
- **M7** paper trading (`/api/paper/*`), **M8** strategy storage+sandbox, **M10** AI assistant, **M9** Next.js PWA frontend.
- **Wrap** auth+billing (free/pro, pro gates on strategy save + AI chat), screener (`/api/screener/scan`), journal (`/api/journal/*`), data export (CSV + `scripts/export_to_git.py`), deploy config (compose + nginx + standalone frontend Dockerfile).
- Commits `1fef617` (wrap backend), `8eb45f7` (frontend tabs), `1258aae` (deploy config).

**Next: Phase 2.**

## Next task: Phase 2 (run in this order)

### Phase 2 — Speed (see ROADMAP.md)
- [ ] **Intraday + replay** — Binance 1m pagination + yfinance 1m (last ~1 week only) → minute-level backtest + paper replay
- [ ] **Screener 2.0** — watchlists, more indicators (RSI/BB/volume), fundamental filters, saved scans
- [ ] **Journal AI review** — Gemini reads journal entries → patterns + feedback (paper-only)
- [ ] **Alerts** — price/indicator push + in-app (Redis-backed)
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
