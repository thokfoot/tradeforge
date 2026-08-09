"""One-shot script: copy all JSON-store data into Postgres tables."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from modules.shared.database import get_session, init_db, use_postgres
from modules.shared.models import (
    AlertNotification,
    AlertRule,
    EducationProgress,
    JournalEntry,
    PaperAccount,
    PaperOrder,
    PaperPosition,
    PaperTrade,
    SavedScan,
    Session as SessionModel,
    Strategy,
    User,
)


def migrate():
    db = get_session()
    data = Path(settings.data_dir)

    # ── Users + Sessions ──
    users_file = data / "auth" / "users.json"
    sessions_file = data / "auth" / "sessions.json"
    if users_file.exists():
        for uid, rec in json.loads(users_file.read_text()).items():
            if db.query(User).filter(User.id == uid).first() is None:
                db.add(User(id=uid, email=rec["email"], password_hash=rec["password_hash"],
                            plan=rec.get("plan", "free"),
                            created_at=rec.get("created_at")))
        db.commit()
        print(f"Migrated users from {users_file}")

    if sessions_file.exists():
        for token, rec in json.loads(sessions_file.read_text()).items():
            if db.query(SessionModel).filter(SessionModel.token == token).first() is None:
                from datetime import datetime
                db.add(SessionModel(token=token, user_id=rec["user_id"],
                                    expires_at=datetime.fromisoformat(rec["expires_at"])))
        db.commit()
        print(f"Migrated sessions from {sessions_file}")

    # ── Journal ──
    journal_dir = data / "journal"
    if journal_dir.exists():
        for f in journal_dir.glob("*.json"):
            uid = f.stem
            for entry in json.loads(f.read_text()):
                eid = entry.get("entry_id", "")
                if db.query(JournalEntry).filter(JournalEntry.entry_id == eid).first() is None:
                    db.add(JournalEntry(
                        entry_id=eid, user_id=uid,
                        trade_id=entry.get("trade_id", ""), note=entry.get("note", ""),
                        symbol=entry.get("symbol", ""), side=entry.get("side"),
                        qty=entry.get("qty"), pnl=entry.get("pnl"),
                        tags=entry.get("tags", []), rating=entry.get("rating"),
                        lesson=entry.get("lesson", ""),
                    ))
        db.commit()
        print(f"Migrated journal entries")

    # ── Alerts ──
    alerts_dir = data / "alerts"
    if alerts_dir.exists():
        for f in alerts_dir.glob("*.json"):
            uid = f.stem
            data_json = json.loads(f.read_text())
            for r in data_json.get("rules", []):
                rid = r.get("rule_id", "")
                if db.query(AlertRule).filter(AlertRule.rule_id == rid).first() is None:
                    db.add(AlertRule(rule_id=rid, user_id=uid, symbol=r["symbol"],
                                     market=r["market"], metric=r["metric"],
                                     condition=r["condition"], value=r["value"],
                                     active=r.get("active", True)))
            for n in data_json.get("notifications", []):
                nid = n.get("id", "")
                if db.query(AlertNotification).filter(AlertNotification.id == nid).first() is None:
                    db.add(AlertNotification(id=nid, user_id=uid, rule_id=n.get("rule_id", ""),
                                              symbol=n.get("symbol", ""), message=n.get("message", "")))
        db.commit()
        print(f"Migrated alerts")

    # ── Screener Scans ──
    screener_dir = data / "screener"
    if screener_dir.exists():
        for f in screener_dir.glob("*.json"):
            uid = f.stem
            for scan in json.loads(f.read_text()):
                sid = scan.get("id", "")
                if db.query(SavedScan).filter(SavedScan.id == sid).first() is None:
                    db.add(SavedScan(id=sid, user_id=uid, name=scan.get("name", ""),
                                     market=scan.get("market", "IN"),
                                     filters=scan.get("filters", {}),
                                     limit=scan.get("limit", 50)))
        db.commit()
        print(f"Migrated saved scans")

    # ── Paper Trading ──
    accounts_dir = data / "accounts"
    if accounts_dir.exists():
        for f in accounts_dir.glob("*.json"):
            uid = f.stem
            ledger = json.loads(f.read_text())
            acct = db.query(PaperAccount).filter(PaperAccount.user_id == uid).first()
            if acct is None:
                db.add(PaperAccount(user_id=uid, balance=ledger.get("balance", 100000)))
            for o in ledger.get("orders", []):
                db.add(PaperOrder(id=o["id"], user_id=uid, symbol=o["symbol"],
                                   side=o["side"], order_type=o["order_type"],
                                   qty=o["qty"], price=o.get("price"),
                                   sl=o.get("sl"), tp=o.get("tp"),
                                   status=o.get("status", "OPEN"),
                                   filled_price=o.get("filled_price"),
                                   filled_at=o.get("filled_at")))
            for t in ledger.get("trades", []):
                db.add(PaperTrade(order_id=t["order_id"], user_id=uid, symbol=t["symbol"],
                                   side=t["side"], qty=t["qty"], price=t["price"],
                                   fees=t["fees"], pnl=t["pnl"],
                                   timestamp=t.get("timestamp")))
            for sym, pos in ledger.get("positions", {}).items():
                db.add(PaperPosition(user_id=uid, symbol=sym, qty=pos["qty"],
                                      avg_price=pos["avg_price"], ltp=pos.get("ltp", 0)))
        db.commit()
        print(f"Migrated paper trading accounts")

    # ── Strategies ──
    strategies_dir = data / "strategies"
    if strategies_dir.exists():
        for f in strategies_dir.glob("*.json"):
            sid = f.stem
            for ver in json.loads(f.read_text()):
                db.add(Strategy(strategy_id=sid, version=ver.get("version", "v1"),
                                code=ver.get("code", ""), params=ver.get("params"),
                                author_user_id=ver.get("author_user_id", "")))
        db.commit()
        print(f"Migrated strategies")

    print("Migration complete.")


if __name__ == "__main__":
    if not use_postgres():
        print("Set DB_BACKEND=postgres and configure DATABASE_URL to migrate.")
        sys.exit(1)
    init_db()
    migrate()
