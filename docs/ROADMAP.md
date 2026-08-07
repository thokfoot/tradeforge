# Roadmap — Phase-by-phase checklist

Status legend: `[ ]` pending · `[x]` done · `[~]` in progress

## Phase 0 — Planning (DONE)

- [x] Market/competitor research (2026): Streak, Tradetron, TradingView, Tickertape, Sensibull, Backtrex, TradeZella, Chartink
- [x] New-trader requirements by skill level (beginner/intermediate/expert)
- [x] Free data source research (India: nse-archives/nsepython/bhavcopy; US: Stooq/Yahoo; Crypto: Binance)
- [x] Lock business decisions (DECISIONS.md)
- [x] Cost model (COSTS.md)
- [x] Modular architecture + isolation rules (ARCHITECTURE.md)
- [x] Data layer design (DATA-LAYER.md)
- [x] Features / pricing / AI-assistant specs (product/)
- [x] Legal notes (LEGAL.md)
- [x] Repo + docs + module skeleton committed

## Phase 0.5 — Data proof-of-concept (NEXT)

- [ ] Confirm Python 3.9+ / pip available
- [ ] India: fetch 5–10 days EOD for a Nifty stock + Nifty 50 index via `nse-archives` (fallback `nsepython`)
- [ ] US: fetch EOD via Stooq (fallback yfinance)
- [ ] Crypto: fetch daily + 1m candles via Binance public API (no key)
- [ ] Record: which sources worked, rate limits, quirks → update DATA-LAYER.md
- [ ] Decide final Phase-1 data provider per market

## Phase 1 — Base (8–10 wk) — India + US + Crypto daily

### Backend foundation
- [ ] Repo scaffold: FastAPI + Postgres + Redis + Parquet, Docker, CI placeholder
- [ ] `shared/contracts` interfaces: MarketDataProvider, Strategy, BacktestEngine, PaperTrader, Analytics, AIAssistant, Auth
- [ ] Config/secrets handling (env-based)

### Data layer
- [ ] MarketDataProvider adapters: NSE(India), Stooq(US), Binance(Crypto)
- [ ] Normalized OHLCV schema + storage (Parquet + Postgres metadata)
- [ ] Symbol master + symbol mapping (NSE vs BSE vs Yahoo ticker formats)
- [ ] Popular-symbols preload + on-demand fetch job

### Backtest engine
- [ ] Event-driven core (bar-by-bar), no look-ahead
- [ ] Cost model: brokerage + STT + GST + SEBI + stamp duty (India), fees (US), maker/taker (crypto)
- [ ] Slippage model
- [ ] Order types: market, limit, SL, bracket
- [ ] Metrics: win rate, profit factor, max drawdown, equity curve, R-multiple, expectancy, per-trade log
- [ ] Reproducible backtests (hash of code+data+params) — unique feature

### Paper trading
- [ ] Live price simulation engine, virtual balance (reset option)
- [ ] Positions/orders/history tracking
- [ ] Parity scoring: backtest vs paper vs live expectations

### Charts + screener
- [ ] TradingView lightweight-charts integration
- [ ] 50+ indicators, multiple timeframes
- [ ] Basic technical + fundamental screener
- [ ] Watchlists

### AI assistant (MVP)
- [ ] Gemini Flash free-tier integration (AI provider adapter — Gemini ↔ Ollama later)
- [ ] Teacher mode: explain RSI, volume, candlesticks etc. (any language, simple words)
- [ ] Listener mode: convert natural language (type or voice) → structured strategy, confirm back in plain words
- [ ] Action mode: create strategy → run backtest → show results (paper-only, every step confirmed)
- [ ] Conversation memory per user

### Users, export, billing
- [ ] Auth (email+password), user profiles
- [ ] "Export my data to my git" feature (owner's data-ownership vision)
- [ ] Daily automatic backups
- [ ] Subscriptions (Razorpay) — basic plans

### Frontend
- [ ] Next.js app + PWA (installable mobile + Windows)
- [ ] Onboarding wizard for beginners (guided)
- [ ] Hinglish/Hindi language toggle (Phase 2 full)
- [ ] Admin/ops dashboard

## Phase 2 — Speed (6–8 wk)

- [ ] Crypto intraday backtesting (Binance free)
- [ ] US intraday (free/cheap source)
- [ ] Trading journal module
- [ ] Alerts (price/indicator, push/in-app)
- [ ] No-code strategy builder (visual)
- [ ] Education content + learning paths
- [ ] Full Hindi UI

## Phase 3 — Full power (8–12 wk)

- [ ] India intraday (bulk archive purchase ~₹5–15k one-time; verify licensing)
- [ ] Options/F&O backtesting (paid data source)
- [ ] Walk-forward + Monte Carlo
- [ ] Expert API access
- [ ] Native mobile + Windows apps (Tauri)
- [ ] Community/marketplace (legal review first)

## Ideas backlog (future)

- Strategy templates library (ICT, ORB, trend-following, mean reversion)
- Parameter optimization grid
- Copy/social trading (legal review first)
- Live market scanning (real-time scanners)
