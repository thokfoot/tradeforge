# NEXT STEPS — start here next session

> If you are an AI agent or the owner opening this project again: read AGENTS.md first, then this file.

## Current state (short)

Phase 0 (Planning) ✅, Phase 0.5 (Data PoC) ✅, and **Phase 1 M1–M10 ✅ (full MVP: backend + API + PWA frontend)**.
- **M1** FastAPI scaffold, **M2** contracts (8 Protocols + 18 models, owner-approved),
  **M3** India adapter (nse-archives), **M4** US (yfinance) + Crypto (Binance) adapters,
  **M5** backtest engine core, **M6** data + backtest API (`/api/symbols`, `/api/ohlcv`, `/api/backtest`),
  **M7** paper trading (`/api/paper/*`), **M8** strategy storage + sandbox (`/api/strategies/*`),
  **M10** AI assistant MVP (`/api/assistant/*`), **M9** Next.js PWA frontend (charts + backtest runner).
- 86 tests green. Live verified end-to-end (API :8000 + frontend :3000, CORS OK).
- Commits `0955737` (M7/M8/M10 + API) + `9250aee` (M9 frontend).

**Next: Phase 1 wrap (auth/billing, VPS deploy), then Phase 2.**

## Next task: Phase 1 wrap (run in this order)

### Phase 1 wrap — make it runnable/deployable
- [ ] Auth + billing (auth_billing module): signup/login, free vs pro plan, plan gates on API
- [ ] VPS deploy: `docker compose up --build` on server, domain + HTTPS, `NEXT_PUBLIC_API_URL` to prod URL
- [ ] Data backfill once (NSE ~1 req/day — slow; US/crypto fast), document Parquet store size
- [ ] README run-guide: local backend + frontend + live demo flow
- [ ] `.env.example` for `GEMINI_API_KEY`, `DATA_DIR`, `NEXT_PUBLIC_API_URL`

### Phase 2 — power features (see ROADMAP.md)
- [ ] Intraday: US/Crypto 1m bars + minute-level paper replay (Binance pagination + yfinance 1m limits known)
- [ ] Screener (multi-symbol scans on the Parquet store)
- [ ] "Export my data to my git" feature (git reimagined decision)
- [ ] Trading journal + AI review
- [ ] Tauri desktop wrapper + notifications

> Full Phase 1/2 scope — see docs/PLAN.md and docs/ROADMAP.md.

## Rules to remember every session

- **Update AGENTS.md + PROGRESS.md + NEXT-STEPS.md at end of session.**
- **Module isolation is the owner's #1 rule:** changes live inside one module; run that module's tests; never let one feature break another.
- Explain things to the owner in simple Hinglish; keep repo docs in English.
- No code comments unless asked. Commit after meaningful milestones only.
