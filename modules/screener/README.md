# module: screener

**Purpose:** Stock screening — technical filters across India, US, and crypto.

**Contract:** uses `MarketDataProvider` (data) — screening logic lives here.

**Implemented (Screener 2.0):**
- `ScreenerService.scan(symbols, filters, limit)` — per-symbol metrics: price, 1d/5d/1m/3m change %, avg volume 20, above/below SMA 20/50/200, RSI(14), Bollinger %B(20,2), volume ratio (last/prev-20 avg), MACD vs signal. Filters: min/max price, min volume, min change_*, min/max RSI, min/max %B, min vol ratio, SMA20/50/200 + MACD booleans. Sortable by any numeric metric.
- `SavedScan` + `ScanStore` (`modules/screener/scans.py`) — per-user JSON saved scans (name, market, filters, limit). API: `POST /api/screener/scans/save`, `GET /api/screener/scans`, `DELETE /api/screener/scans/{id}`, `POST /api/screener/scans/{id}/run` — all auth-gated (login).
- No fundamental filters yet — no free fundamental data source; revisit when a provider exists.

**Later:** alerts on screens, real-time scanning, watchlists.

**Isolation:** Reads data via contract; owns saved-scan storage exclusively.

**Status:** Implemented (Screener 2.0).
