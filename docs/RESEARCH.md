# Research Notes (2026) — market, competitors, data sources, new-trader needs

> Compiled from public sources during planning (Aug 2026). Prices/limits change — verify before relying.

## 1. New-trader requirements by skill level

| Level | What they need | Skill set to develop |
|---|---|---|
| **Beginner** | Guided onboarding, simple UI, virtual money/demo, watchlists, basic charts, education (RSI? volume? candles?), no-code | Reading candles, SL/TP, risk basics, position sizing |
| **Intermediate** | Strategy testing, backtesting, 100+ indicators, alerts, trading journal, multiple timeframes, no-code builder | Technical analysis, journaling discipline, risk management |
| **Expert** | Python/code mode, parameter optimization, options, portfolio backtests, API, data export, low latency | Coding, quant skills, execution realism |

Common must-haves across platforms: charting (candles + indicators + drawing), screener (technical+fundamental), backtesting with realistic costs, paper trading, trading journal, alerts, watchlists, education, community, data export, mobile access.

## 2. Competitor landscape & pricing (2026)

| Platform | Price | Coverage | Notes / gaps |
|---|---|---|---|
| Zerodha Streak | Free (Zerodha users) / ₹500–1400/mo | India, no-code algo | No US/crypto; options weak; free tier 5 live deploys |
| Tradetron | Free–₹15,000/mo (Retail ~₹1,000/mo) | India, marketplace | Expensive at scale; India only |
| TradingView | Free–$29.95/mo | Global | Best charts; Pine coding required; no India F&O |
| Tickertape | ~₹299/mo Pro | India research/screeners | No backtesting |
| Sensibull | ~₹1,500/mo | India options | Options only |
| Backtrex | €29/mo | No-code backtesting | No paper trading/mobile focus |
| Chartink | screeners | India | Screeners only |
| TradeZella | paid | Journal + backtest + 500 broker integrations | Journal strength |

**Wedge:** No single tool covers India + US + crypto + backtest + paper + journal + education in one subscription. Plus our teaching AI assistant (voice + any language) doesn't exist anywhere.

## 3. Free data sources (verified-ish, 2026)

### India (NSE/BSE)
- **`nse-archives`** (PyPI, MIT) — ✅ VERIFIED (2026-08-07): bhavcopy per trading day (all stocks OHLC+volume+delivery) + 163 indices (Nifty 50 etc. with P/E). Historical dates work; backfill = 1 request/day. No split-adjustment info → adjustment policy needed.
- **`nsepython`** (PyPI) — unofficial NSE REST wrapper; live + historical; slower single-threaded.
- **NSEPy / `swapniljariwala/nsepy`** — older, historical stocks/indices/F&O, needs maintenance care.
- **bhavcopy** — daily OHLC for all traded stocks (free daily file). Good for EOD.
- **yfinance** — Indian stocks limited (~4yr), inconsistent.
- **Fundamentals (point-in-time):** free options suffer look-ahead + survivorship bias. Flag for later (paid PIT source).
- **Intraday (India):** NO official free bulk. Third-party archives ~₹5–15k one-time or ~₹1–3k/mo. Licensing/commercial-use unclear → Phase 3 + verify.

### US
- **Stooq** — ⚠️ VERIFIED DEAD for automated access (2026-08-07: HTTP 404 on all symbol variants). Do not plan on it.
- **Yahoo Finance (yfinance)** — ✅ VERIFIED works: daily full history (~10y+), 1h = ~1yr, **1m = only last ~5–7 days** (Yahoo limit). Free, unofficial, throttled, ToS gray → primary US source now, licensed upgrade later.
- **Alpha Vantage** — free tier 25 calls/day (too low for multiuser).
- **Financial Modeling Prep / TwelveData** — free tiers small; paid for production (upgrade path).
- **Polygon.io / Alpaca** — intraday; Polygon paid ~$30+/mo; Alpaca free tier limited. Needed only for US 1m backtests (Phase 3+).

### Crypto
- **Binance public API** — free, no key for klines (`api.binance.com/api/v3/klines`). Daily + 1m + monthly archives at `data.binance.vision` (free, checksummed, deep history). ← Best crypto source, free even intraday.
- **CoinGecko** — free tier 10k calls/mo, 17k+ coins; keyless demo. Good for coverage/lookup.
- **CoinPaprika** — 1yr daily free, no key. Limited depth.

## 4. Backtest engine landscape (for our own engine design)

- **event-driven** (bar-by-bar, realistic, prevents look-ahead): backtrader (abandoned upstream), zipline-reloaded (slow), NautilusTrader (Rust core, modern, multi-asset), backtesting.py (simple).
- **vectorized** (fast, less realistic): vectorbt (active, Apache + Commons Clause — commercial resale restricted!).
- **Recommendation:** build our own lean event-driven core (gives full control over Indian cost model + reproducibility) informed by backtesting.py patterns; optionally use numpy/pandas. Do NOT embed GPL/Commons-Clause engines into a commercial product without review.

## 5. Key numbers (for context)

- 74–89% of retail CFD accounts lose money (ESMA) — backtest realism matters.
- ~70–80% of day traders lose money, mostly year one.
- TradingView paper: $100k virtual balance, resettable; no options.
- SEBI algo trading framework fully mandatory Apr 1, 2026 (relevant only if we ever do live execution).
- India intraday storage: all stocks ≈ 1TB; popular ~200 stocks + indices ≈ 100GB (Parquet compressed).
