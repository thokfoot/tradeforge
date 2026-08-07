# Master Plan — trade-forge

Universal backtester + paper trading platform (India + US + Crypto). One subscription replaces 4 tools.
Status: **Phase 0 complete (planning). Next: data PoC → Phase 1.**

## Vision (locked with owner)

- Every customer gets: backtesting + paper trading + charts + screeners + journal + education + AI assistant — one subscription.
- No customer leaves with an unfulfilled wish ("koi customer khali nahi jayega").
- Markets: India (NSE/BSE — all stocks, Nifty 50, Bank Nifty, indices) + US + Crypto, together from Phase 1 (daily).
- Free data sources to start, provider-swappable. Free/cheap AI (Gemini Flash free tier), provider-swappable.
- Beginner → expert all served. Teaching + voice + any language is a core differentiator.
- Modular: changing one module must never disturb another (contracts + per-module tests).

## Roadmap summary

| Phase | What ships | Est. cost/mo | Notes |
|---|---|---|---|
| **0 — Planning** | Docs, decisions, research, repo skeleton | ₹0 | **DONE** |
| **0.5 — Data PoC** | Test free data sources end-to-end | ₹0 | Next up |
| **1 — Base (8–10 wk)** | India+US+Crypto DAILY backtest, paper trading, charts, screener, data export. Web + PWA. | ₹0–500 | First customers |
| **2 — Speed (6–8 wk)** | Crypto + US intraday, journal, alerts, no-code builder, education | ~₹2,000 | |
| **3 — Full power (8–12 wk)** | India intraday (paid archive ~₹5–15k one-time), options, advanced analytics, native apps | ~₹5,000 | |

## Phase 1 scope (concrete)

- **Markets:** India NSE/BSE daily EOD (all stocks + Nifty 50, Bank Nifty, all indices), US daily EOD, Crypto daily.
- **Backtester:** event-driven, realistic Indian cost model (brokerage, STT, GST, SEBI fees, stamp duty) + slippage. This realism is the #1 trust moat.
- **Paper trading:** real-time simulation on live prices, resettable virtual balance, full order types (market/limit/SL/bracket).
- **Charts:** candlesticks, multiple timeframes, 50+ indicators, drawing tools (TradingView lightweight-charts).
- **Screener:** technical + fundamental basic filters.
- **Data export:** CSV + "export my data to my own git" feature (owner's data-ownership vision).
- **AI assistant:** 3-in-1 (teacher + listener + doer), text + voice, any language, paper-only, confirms every step. Gemini Flash free tier.
- **Platforms:** Web + PWA (installable on mobile + Windows, ₹0 store fees). Native apps in Phase 3.
- **Auth/billing:** email+password to start, subscriptions later (Razorpay).

## Phase 2 scope

- Crypto + US intraday backtesting. Journal module. Alerts (price/indicator/SMS-ish/push). No-code strategy builder. Education content. Hindi UI toggle.

## Phase 3 scope

- India intraday (purchase bulk archive ~₹5–15k one-time). Options/F&O (paid data source). Walk-forward/Monte Carlo. API access for experts. Native mobile + Windows apps. Community/marketplace (legal review first).

## Out of scope (until later / never)

- Real/live order execution (SEBI algo rules 2026 — would require compliance). Paper trading only.
- Paid cash-prize competitions (regulated) unless legal review passes.
