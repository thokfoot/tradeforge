"""Seed a demo Pro account with sample data for first-customer onboarding."""
import os
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from modules.auth_billing.service import AuthService
from modules.auth_billing.store import UserStore
from modules.trading_journal.store import JournalStore

DATA_DIR = os.environ.get("DATA_DIR", "data")


def main():
    user_store = UserStore(pathlib.Path(DATA_DIR) / "auth")
    auth = AuthService(user_store)
    journal_store = JournalStore(pathlib.Path(DATA_DIR) / "journal")
    email = "demo@tradeforge.in"
    password = "tradeforge123"

    try:
        user = auth.register(email, password)
    except ValueError:
        existing = user_store.find_by_email(email)
        if existing:
            print(f"Demo user already exists ({existing['email']}), skipping registration.")
            user = auth.get_user(existing["id"])
        else:
            raise

    if user.plan != "pro":
        auth.create_subscription(user.id, "pro")
        print(f"Upgraded {email} to Pro.")

    sample_entries = [
        ("AAPL BUY 10 @ 314.08", "Bought AAPL at daily support after RSI bounce from 40. Volume was decent.",
         "AAPL", "BUY", None, ["momentum", "support"], 3, "RSI bounce setups work well on AAPL daily."),
        ("AAPL SELL 10 @ 320.15", "Sold AAPL for +6.07 per share. Exit at resistance near 320.",
         "AAPL", "SELL", 5973, ["profit-taking", "resistance"], 4, "Took profit at resistance. Could have held for more."),
        ("TSLA BUY 5 @ 245.90", "Bought TSLA dip. Elon tweet caused panic sell — trying reversal play.",
         "TSLA", "BUY", None, ["reversal", "news"], 2, "Don't chase news-based dips without confirmation."),
        ("TSLA SELL 5 @ 238.40", "Cut losses on TSLA. Reversal didn't come. Lost 7.50 per share.",
         "TSLA", "SELL", -3750, ["stop-loss", "discipline"], 5, "Good: cut loss early. Bad: entered without confirmation."),
        ("RELIANCE BUY 20 @ 1334.80", "RELIANCE at SMA 50 support. Strong delivery volume. 3% dividend yield cushion.",
         "RELIANCE", "BUY", None, ["value", "delivery"], 4, "Good entry on Nifty 50 heavyweight. Wait for 1400 target."),
        ("BTCUSDT BUY 0.1 @ 64958", "Crypto allocation. BTC above 200-day MA. Halving supply squeeze thesis.",
         "BTCUSDT", "BUY", None, ["crypto", "trend"], 3, "Small allocation only. Crypto is volatile."),
    ]

    for trade_id, note, sym, side, pnl, tags, rating, lesson in sample_entries:
        qty_part = trade_id.split()[2]
        try:
            qty = int(qty_part)
        except ValueError:
            qty = int(float(qty_part))
        journal_store.append(
            user.id,
            {
                "entry_id": str(uuid.uuid4())[:12],
                "user_id": user.id,
                "trade_id": trade_id,
                "note": note,
                "symbol": sym,
                "side": side,
                "qty": qty,
                "pnl": pnl,
                "tags": tags,
                "rating": rating,
                "lesson": lesson,
            },
        )

    print(f"Added {len(sample_entries)} sample journal entries.")
    entries = journal_store.load(user.id)
    print(f"Demo account ready: {len(entries)} journal entries | plan={user.plan} | {email} | password={password}")


if __name__ == "__main__":
    main()
