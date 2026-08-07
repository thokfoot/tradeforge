# Legal & Compliance Notes

> Educational planning notes. NOT legal advice. Get a real review before launch (owner can use Jio Gemini Pro or cheap counsel for a first pass).

## Positioning (core)
- Product = **simulation/education software only**. No real order execution, no brokerage, no advisory.
- Required on every results page: risk warning + "past performance does not guarantee future results".
- Clear "educational use only" framing in ToS/onboarding (also shields free-data licensing).

## SEBI — algo trading rules (2026)
- SEBI's algorithmic trading framework became **fully mandatory April 1, 2026** — applies to order placement/execution via algos. We do **not** place real orders (paper only), so it should not apply directly — but our "strategy deployment" language must not imply live execution.
- If we EVER add live execution: requires broker partner + SEBI algo compliance. Defer; revisit with legal.
- Do not market as "investment advice" (would trigger SEBI RA/IA registration). We sell a tool.

## Data licensing (real risk — must manage)
- **NSE/BSE:** exchange data redistribution is restricted; no official free API. Unofficial scrapers/archives (nsepython, nse-archives, bhavcopy mirrors) are gray for commercial redistribution. Mitigation: "educational use" framing, avoid reselling raw data dumps, plan licensed vendor upgrade (Phase 3 for intraday).
- **Yahoo Finance:** scraping/unofficial API violates ToS. Use only as temporary fallback; prefer Stooq (free CSV) and upgrade to licensed (FMP/TwelveData) when revenue allows.
- **Binance:** public market data API is freely usable; still require attribution care + terms check.
- **Crypto per-region:** India RBI stance has varied; crypto trading is legal in India but taxed; US crypto regulation evolving. We only show data + simulation — document any disclaimers needed.

## Payments & privacy
- India payments: Razorpay (compliant, standard). PCI handled by provider (never store card data).
- Data protection: user data export right baked in (our "export to my git" feature supports it). Privacy policy required; server hosting location + vendor DPAs.

## Paper-trading competitions / prizes
- Cash prizes for simulated trading can be treated as gambling/skill-game in some jurisdictions → **do NOT do this without legal review.** (D-12)

## Trademarks
- "Nifty 50", "Bank Nifty", "NSE", "BSE" are trademarks — use descriptively ("Nifty 50 index data") with disclaimers; avoid implying official affiliation.

## To launch checklist
- [ ] Disclaimer + ToS + Privacy policy drafted
- [ ] Risk warnings on all results/backtest/paper screens
- [ ] "Educational use only" wording
- [ ] Data source attribution/terms review per provider
- [ ] Legal review pass (cheap counsel or AI-assisted first draft)
