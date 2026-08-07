# module: auth-billing

**Purpose:** Users, login, sessions, subscriptions, payments.

**Contract:** `AuthService` (see `../shared/contracts/README.md`).

**Phase 1:** email+password registration/login, JWT sessions, user profiles.
**Phase 1.5+:** Razorpay subscriptions (Free/Pro/Expert), invoices, usage quotas (backtests/day for free tier).

**Isolation:** Owns users + subscription tables exclusively. No other module writes to them.

**Security:** passwords hashed (bcrypt/argon2), no card data stored (PCI via Razorpay), env-based secrets.

**Status:** Planning.
