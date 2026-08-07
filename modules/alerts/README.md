# module: alerts — price & RSI alert rules

**Purpose:** Let users create alert rules ("if AAPL price goes above 200" or "if BTCUSDT RSI(14) goes below 30") and get in-app notifications when the condition fires. One-shot rules: once triggered, the rule deactivates so it can't spam.

**Contract:** `AlertService` (see `../shared/contracts/README.md`). Models `AlertRule` + `AlertNotification` live in shared contracts.

## Isolation (owner's #1 rule)
- Everything lives in this module: `AlertStore` (per-user JSON: rules + notifications) + `AlertService` (create/list/delete/notifications/clear/check_user/check_all).
- No cross-module imports. RSI(14) is computed with a local copy of the Wilder formula so the module never touches screener internals.
- The app talks to it only through the `AlertService` contract.

## Evaluation
- `check_user(user_id, provider_for)` — evaluates that user's active rules against live data (PRICE via `fetch_quote`, RSI via daily `fetch_ohlcv`). Provider errors on one rule are skipped, never crash the check.
- `check_all(provider_for)` — iterates every user that has rules.
- On hit: rule marked `active=False` + a `AlertNotification` is appended (capped at 200).

## API + worker
- `app/api/alerts.py` — `POST /api/alerts` (create, login), `GET /api/alerts`, `DELETE /api/alerts/{rule_id}`, `GET /api/alerts/notifications`, `POST /api/alerts/notifications/clear`, `POST /api/alerts/check`. All login-gated.
- Background loop in `app/main.py` lifespan: runs `check_all` every `alert_check_interval_seconds`, only when `settings.alerts_enabled` (off by default, enable on the VPS).

**Status:** Live. 15 tests (11 module + 4 API).
