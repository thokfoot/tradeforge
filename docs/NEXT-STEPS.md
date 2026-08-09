# NEXT STEPS — start here next session

> If you are an AI agent or the owner opening this project again: read AGENTS.md first, then this file.

## Current state (short)

**Phase 1 + 2 + 3 COMPLETE. Local release candidate verified.** 236 tests green.
- Security hardening: path traversal closed in all file stores; journal/paper/assistant endpoints now login-gated (user_id from token, never from client); watchlists 422 bug + sandbox `exit` blocking fixed.
- Paper trading upgraded: chart-native bracket orders (draggable SL/TP lines on the position chart, right-click Close/Reverse via `PaperChart.tsx`), reset-to-any-amount (`POST /api/paper/reset?amount=`, `setLevels` endpoint).
- Tauri .exe built (21.8 MB, Win x64)
- Education tab (12 lessons EN/HI)
- Watchlists (add/remove per market, login-gated)
- Full Hindi i18n (EN/HI toggle everywhere)
- Onboarding wizard (5-step guided flow)
- Admin dashboard (health + status)
- Postgres migration ready (DB_BACKEND=postgres)
- Demo account ready (demo@tradeforge.in / tradeforge123)
- Local production stack verified (`uvicorn` without reload + standalone Next server)
- India local dataset ready for testing: 3,462 NSE stock/index files after a 30-day all-stock backfill; major indices and representative Nifty/Bank constituents have a 90-day window
- US and Crypto local datasets verified
- Desktop/mobile UI acceptance pass completed: line navigation, hover states, animations, command palette, floating AI assistant, market/index filters, strategy templates, and sticky controls
- VPS deploy scripts ready (deploy.sh, nginx SSL)

## Only remaining

- [ ] **VPS test** — copy repo to real cloud VPS, `bash scripts/deploy.sh --setup`, set `DB_BACKEND=postgres`, `python scripts/migrate_to_pg.py`, then `--ssl yourdomain.com`
- [x] **Local data backfill** — 30-day all-NSE-stock dataset plus 90-day representative/index dataset completed; `--days`, `--all-stocks`, holiday handling, and batch writes added to `scripts/backfill_india.py`
- [ ] **Optional deep data backfill** — run a longer India history if the launch needs more than the local 90-day research window
- [ ] **Tauri sign** — code-sign the .exe for Windows distribution (optional)

## Next task: Production launch (only after local sign-off)

- [x] Local production build and smoke checks
- [x] Beginner, mid-level, and pro feature paths verified locally
- [ ] Choose VPS and domain
- [ ] Set production secrets and switch to Postgres
- [ ] Deploy Docker stack and HTTPS
- [ ] Run production smoke tests and backups

## Phase 2 historical record

### Phase 2 — Speed (see ROADMAP.md) — ALL DONE
- [x] **Intraday + replay** — 1m/1h bars, minute backtest + paper replay
- [x] **Screener 2.0** — indicators (RSI/BB/vol-ratio/MACD/SMA20) + saved scans
- [x] **Journal AI review** — Gemini reads journal entries → patterns + feedback
- [x] **Alerts** — price + RSI one-shot rules, in-app notifications, background loop
- [x] **No-code strategy builder** — visual blocks → generated `signals` code
- [x] **Tauri desktop** — config + Rust backend + notification plugin written (needs Rust installed to build .exe)
- [x] **VPS deploy** — `scripts/deploy.sh` + SSL nginx config + compose updates (needs VPS to test)

### Phase 1 leftovers → moved to Phase 3
- [ ] VPS test (Docker not on dev machine — script + config ready)
- [x] Local India data backfill for representative symbols and indexes; deeper history remains optional
- [x] Seed a demo Pro account for the first customer
- [x] Postgres migration prepared; production adoption waits for the VPS

> Full Phase 2/3 scope — see docs/PLAN.md and docs/ROADMAP.md.

## Rules to remember every session

- **Update AGENTS.md + PROGRESS.md + NEXT-STEPS.md at end of session.**
- **Module isolation is the owner's #1 rule:** changes live inside one module; run that module's tests; never let one feature break another.
- Explain things to the owner in simple Hinglish; keep repo docs in English.
- No code comments unless asked. Commit after meaningful milestones only.
