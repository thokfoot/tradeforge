# Decisions Log (ADR-style) — every decision + why

Append new decisions here. Each entry: **Decision → Reason → Impact**. This is the traceable record of why we chose what we chose.

---

## D-01: Git per customer → REIMAGINED (not git-as-primary-storage)
- **Decision:** Customer data lives in our Postgres/Parquet runtime storage. Git stores strategy code (perfect fit — small text files) + a "export my data to my own git" feature for customers. No customer-owned git repo as the primary database.
- **Reason:** Git is a code version-control tool, not a database. Backtests generate data on every run → repo bloat, concurrent-write/locking problems, credential management security risk, 1000 customers = 1000 repos = ops nightmare. The owner's real goals — data ownership + traceability — are met by: strategy versioning in git + export feature + reproducible backtests + git history on everything.
- **Impact:** Cheaper, safer, scalable. Same customer-facing benefits (data is theirs, portable, auditable).

## D-02: Home PC as server → NO. Cloud VPS instead.
- **Decision:** Host on a cloud VPS. Start Oracle Cloud Free Tier (₹0) or Hetzner (~₹400–600/mo). Never the owner's home PC.
- **Reason:** Uptime, data-loss risk (hard drive), unreliable home internet, security for customer data + payments, 24/7 monitoring. Customers only care that the app always works and data is never lost.
- **Impact:** Cost ₹0–500/mo. Reliable, secure, scalable (₹1500/mo at 100 users, ₹3000–5000/mo at 1000).

## D-03: Not a "cheapest in market" race
- **Decision:** Freemium pricing; Pro target ₹99–199/mo. Compete on bundling (1 sub replaces 4 tools) + backtest realism + teaching, not on being the cheapest.
- **Reason:** Streak has a free tier for Zerodha users; a price war is a race to the bottom. Value pricing is sustainable; ₹199 × 10 customers pays the server.
- **Impact:** Sustainable margins, funds future features.

## D-04: All markets daily in Phase 1; intraday phased
- **Decision:** Phase 1 = India + US + Crypto, DAILY (EOD) data. Intraday: crypto/US in Phase 2 (free/cheap), India intraday Phase 3 (paid archive ~₹5–15k one-time).
- **Reason:** India intraday is the only expensive data. Phasing lets revenue arrive before spending; no customer is empty-handed (daily works from day 1, intraday "coming soon").
- **Impact:** Lowest-risk start, revenue covers Phase 3 data purchase.

## D-05: Popular-symbols always-ready + on-demand fetch
- **Decision:** Store intraday/full data for popular symbols (Nifty 50, F&O stocks ~200, indices, top US, major crypto); fetch any other symbol on-demand when a customer opens it.
- **Reason:** Storage for "everything intraday" = ~1TB; popular-only = ~100GB. Customer cannot tell the difference.
- **Impact:** Saves ₹0–1000s/mo in storage. Same UX.

## D-06: AI assistant — 3-in-1, provider-adapter
- **Decision:** In-app AI agent with three modes (Teacher: explains RSI/volume/etc.; Listener: turns spoken/typed words in any language into a structured strategy; Doer: sets up strategy, backtests, paper-trades). Start with Gemini Flash free-tier API. AI provider is an adapter (Gemini ↔ Ollama self-host ↔ paid), so we can switch later.
- **Reason:** Teaching + voice + any language is our biggest differentiator vs Streak/Tradetron (no education). Free tier = ₹0 start. Adapter = no lock-in (owner asked about Ollama; quality of 7B open models is weak for Hindi/agent work, bigger models need ₹10–30k/mo GPU — so Gemini first, hybrid later).
- **Impact:** ₹0–3/customer/month AI cost. Fully isolated module.
- **Note:** Owner's Jio free Gemini Pro is for personal use only — it does not provide an API key; the app uses the Gemini API (free tier) instead.

## D-07: Backtest realism is the #1 moat
- **Decision:** Event-driven backtest engine with full Indian cost model (brokerage, STT, GST, SEBI charges, stamp duty) + slippage + realistic fill modeling. Paper trading simulates real conditions. Backtest↔paper↔live parity scoring.
- **Reason:** Research shows divergence >2% between backtest and live invalidates a strategy for scalping; 74–89% of retail CFD accounts lose money and bad backtests cause false confidence. Realism = trust = retention.
- **Impact:** Slower to build but the defensible differentiator.

## D-08: PWA first, native apps Phase 3
- **Decision:** Web + PWA (installable to home screen on mobile and Windows, ₹0 store fees). Native apps later.
- **Reason:** Google Play ₹3500 one-time + Apple ₹6700/yr + 30% revenue cut. PWA delivers "installable app" experience for ₹0.
- **Impact:** Saves thousands, launches faster.

## D-09: AI provider choice — Gemini Flash free tier first
- **Decision:** Gemini Flash API (free tier) for the AI assistant; adapter pattern allows switching to Ollama (self-host) or paid models later.
- **Reason:** Best Hindi/Hinglish + agent quality at ₹0. Ollama small models (7B) are weak; good open models need expensive GPU. Owner's Jio Gemini Pro ≠ API.
- **Impact:** ₹0 start, switchable later.

## D-10: Free data sources with strict licensing caution
- **Decision:** Start with free sources (India: nse-archives/nsepython/bhavcopy; US: Stooq/Yahoo; Crypto: Binance). Architecture is provider-agnostic. All "free" sources that lack commercial redistribution rights are framed as "educational use" and flagged in LEGAL.md; plan a licensed source upgrade path.
- **Reason:** NSE/Yahoo ToS restrict commercial redistribution — a real risk for a paid product.
- **Impact:** Low cost now, compliance risk managed, easy to upgrade.

## D-11: Paper trading only — no live execution
- **Decision:** The product is simulation/education only. No real order execution now or in the near term.
- **Reason:** SEBI algorithmic trading framework (mandatory Apr 1, 2026) adds compliance burden for live algo execution; paper trading is safer to launch. Revenue model works on subscriptions, not execution.
- **Impact:** Faster, cheaper, lower risk launch. Live execution = possible future pivot with legal review.

## D-12: No cash-prize competitions (for now)
- **Decision:** Do not run paid paper-trading competitions with real prizes until legal review.
- **Reason:** Such schemes can be regulated (gambling/skill-game laws vary).
- **Impact:** Avoids regulatory exposure in MVP.
