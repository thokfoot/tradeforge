# module: notifications

**Purpose:** Alerts and notifications — in-app, push, and later email/SMS/WhatsApp.

**Contract:** `NotificationService` (see `../shared/contracts/README.md`).

**Phase 2:** price alerts (crossing level), indicator alerts, strategy signals, backtest-done notifications.

**Design:** publishes via queue (Redis); channels are adapters (in-app first, push later) so adding a channel never touches other modules.

**Isolation:** Owns alert rules + delivery logs exclusively.

**Status:** Planning.
