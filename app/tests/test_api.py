import types

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from modules.shared.contracts import SymbolInfo


def pro_token(monkeypatch, tmp_path):
    from app.api import deps
    from modules.auth_billing import AuthService, UserStore

    service = AuthService(UserStore(tmp_path / "auth"))
    monkeypatch.setattr(deps, "_auth_service", service)
    service.register("pro@test.com", "password123")
    user_id = service._store.find_by_email("pro@test.com")["id"]
    service.create_subscription(user_id, "pro")
    return service.login("pro@test.com", "password123").token


PRO_HEADERS = {"Authorization": "Bearer PRO_TOKEN"}


class FakeProvider:
    def __init__(self, df: pd.DataFrame):
        self._df = df
        self._symbols = [
            SymbolInfo(
                symbol="TEST",
                market="IN",
                exchange="NSE",
                name="Test",
                currency="INR",
                instrument_type="stock",
            )
        ]

    def get_symbols(self):
        return self._symbols

    def fetch_ohlcv(self, symbol, interval, start, end):
        return self._df

    def fetch_quote(self, symbol):
        return types.SimpleNamespace(price=102.5)


@pytest.fixture
def fake_provider():
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    close = pd.Series(range(100, 110), index=idx, dtype=float)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )
    return FakeProvider(df)


@pytest.fixture
def client(fake_provider, monkeypatch):
    from app.api import deps

    monkeypatch.setattr(deps, "provider_for", lambda market: fake_provider)
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_symbols(client):
    resp = client.get("/api/symbols", params={"market": "IN"})
    assert resp.status_code == 200
    assert resp.json()[0]["symbol"] == "TEST"


def test_ohlcv(client, fake_provider):
    resp = client.get("/api/ohlcv/TEST", params={"market": "IN"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["bars"]) == 10
    assert body["bars"][0]["close"] == 100.0
    assert set(body["bars"][0]) == {"date", "open", "high", "low", "close", "volume"}


def test_ohlcv_empty_returns_404(fake_provider, monkeypatch):
    fake_provider._df = pd.DataFrame(
        columns=["open", "high", "low", "close", "volume"]
    ).set_index(pd.DatetimeIndex([], name="date"))
    from app.api import deps

    monkeypatch.setattr(deps, "provider_for", lambda market: fake_provider)
    resp = TestClient(app).get("/api/ohlcv/TEST", params={"market": "IN"})
    assert resp.status_code == 404


def test_backtest(client):
    code = (
        "signals = (data['close'] > data['close'].rolling(3).mean()).astype(int)"
    )
    payload = {
        "market": "IN",
        "symbol": "TEST",
        "interval": "1d",
        "start": "2024-01-01",
        "end": "2024-01-15",
        "code": code,
        "initial_capital": 100000.0,
        "position_size": 10.0,
    }
    resp = client.post("/api/backtest", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_hash"]
    assert len(body["equity_curve"]) == 10
    assert body["metrics"]["total_trades"] >= 0
    assert body["symbol"] == "TEST"


def test_backtest_invalid_interval(fake_provider, monkeypatch):
    from app.api import deps

    def failing(*a, **k):
        raise ValueError("unsupported interval")

    fake_provider.fetch_ohlcv = failing
    monkeypatch.setattr(deps, "provider_for", lambda market: fake_provider)
    resp = TestClient(app).post(
        "/api/backtest",
        json={
            "market": "IN",
            "symbol": "TEST",
            "start": "2024-01-01",
            "end": "2024-01-15",
            "code": "signals = data['close'] * 0",
        },
    )
    assert resp.status_code == 422


def test_paper_order_buy_fills(client, monkeypatch):
    from app.api import deps
    from modules.paper_trading.store import AccountStore

    monkeypatch.setattr(deps, "_paper_store", AccountStore(None))
    resp = client.post(
        "/api/paper/order",
        json={"user_id": "u1", "market": "IN", "symbol": "TEST", "side": "BUY", "qty": 10},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "FILLED"
    acc = client.get("/api/paper/account", params={"user_id": "u1"}).json()
    assert acc["balance"] == 100000.0 - 10 * 102.5
    assert acc["equity"] == pytest.approx(100000.0)


def test_paper_order_sell_without_position_rejected(client, monkeypatch):
    from app.api import deps
    from modules.paper_trading.store import AccountStore

    monkeypatch.setattr(deps, "_paper_store", AccountStore(None))
    resp = client.post(
        "/api/paper/order",
        json={"user_id": "u1", "market": "IN", "symbol": "TEST", "side": "SELL", "qty": 5},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"


def test_paper_reset(client, monkeypatch):
    from app.api import deps
    from modules.paper_trading.store import AccountStore

    monkeypatch.setattr(deps, "_paper_store", AccountStore(None))
    client.post(
        "/api/paper/order",
        json={"user_id": "u1", "market": "IN", "symbol": "TEST", "side": "BUY", "qty": 10},
    )
    resp = client.post("/api/paper/reset", params={"user_id": "u1"}).json()
    assert resp["balance"] == 100000.0
    assert resp["equity"] == 100000.0


def test_strategy_save_and_versions(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.strategy_engine import StrategyService, StrategyStore

    token = pro_token(monkeypatch, tmp_path)
    monkeypatch.setattr(
        deps, "_strategy_service", StrategyService(StrategyStore(tmp_path / "strategies"))
    )
    payload = {
        "id": "s1",
        "code": "signals = (data['close'] > data['close'].rolling(3).mean()).astype(int)",
    }
    resp = client.post(
        "/api/strategies/save", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["version"] == "v1"
    assert resp.json()["author_user_id"] == pro_token_user_id(monkeypatch, tmp_path)
    versions = client.get("/api/strategies/s1/versions").json()
    assert versions == ["v1"]


def pro_token_user_id(monkeypatch, tmp_path):
    from app.api import deps

    return deps.auth_service()._store.find_by_email("pro@test.com")["id"]


def test_strategy_save_requires_pro(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.auth_billing import AuthService, UserStore
    from modules.strategy_engine import StrategyService, StrategyStore

    service = AuthService(UserStore(tmp_path / "auth"))
    monkeypatch.setattr(deps, "_auth_service", service)
    service.register("free@test.com", "password123")
    token = service.login("free@test.com", "password123").token
    monkeypatch.setattr(
        deps, "_strategy_service", StrategyService(StrategyStore(tmp_path / "strategies"))
    )
    resp = client.post(
        "/api/strategies/save",
        json={"id": "s1", "code": "signals = data['close'] * 0"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_strategy_save_requires_auth(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.strategy_engine import StrategyService, StrategyStore

    monkeypatch.setattr(
        deps, "_strategy_service", StrategyService(StrategyStore(tmp_path / "strategies"))
    )
    resp = client.post("/api/strategies/save", json={"id": "s1", "code": "signals = 0"})
    assert resp.status_code == 401


def test_strategy_save_invalid_returns_422(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.strategy_engine import StrategyService, StrategyStore

    token = pro_token(monkeypatch, tmp_path)
    monkeypatch.setattr(
        deps, "_strategy_service", StrategyService(StrategyStore(tmp_path / "strategies"))
    )
    resp = client.post(
        "/api/strategies/save",
        json={"id": "s1", "code": "x = 1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_assistant_chat_requires_pro(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.ai_assistant import AIAssistantService

    class FakeGen:
        def generate(self, prompt):
            return "RSI momentum ka indicator hai..."

    token = pro_token(monkeypatch, tmp_path)
    monkeypatch.setattr(deps, "_assistant_service", AIAssistantService(FakeGen()))
    resp = client.post(
        "/api/assistant/chat",
        json={"user_id": "u1", "message": "RSI kya hai?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "RSI" in resp.json()["text"]


def test_assistant_chat_unauth_401(client, monkeypatch):
    from app.api import deps
    from modules.ai_assistant import AIAssistantService

    monkeypatch.setattr(deps, "_assistant_service", AIAssistantService(type("G", (), {"generate": lambda self, p: "x"})()))
    resp = client.post(
        "/api/assistant/chat", json={"user_id": "u1", "message": "hi"}
    )
    assert resp.status_code == 401


def test_journal_review_pro(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.ai_assistant import AIAssistantService
    from modules.trading_journal import JournalService, JournalStore

    monkeypatch.setattr(
        deps,
        "_journal_service",
        JournalService(JournalStore(tmp_path / "journal")),
    )
    deps._journal_service.add_entry(
        user_id="demo",
        trade_id="t1",
        note="bought breakout, held well",
        symbol="AAPL",
        pnl=120.0,
        tags=["momentum"],
    )
    monkeypatch.setattr(
        deps,
        "_assistant_service",
        AIAssistantService(type("G", (), {"generate": lambda self, p: "Good discipline: AAPL hold."})()),
    )
    token = pro_token(monkeypatch, tmp_path)
    resp = client.post(
        "/api/journal/review",
        json={"user_id": "demo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["entries"] == 1
    assert "AAPL" in body["text"]


def test_journal_review_unauth_401(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.ai_assistant import AIAssistantService
    from modules.trading_journal import JournalService, JournalStore

    monkeypatch.setattr(
        deps,
        "_journal_service",
        JournalService(JournalStore(tmp_path / "journal")),
    )
    monkeypatch.setattr(
        deps,
        "_assistant_service",
        AIAssistantService(type("G", (), {"generate": lambda self, p: "x"})()),
    )
    resp = client.post("/api/journal/review", json={"user_id": "demo"})
    assert resp.status_code == 401


def test_alerts_crud(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.alerts import AlertService, AlertStore

    service = AlertService(AlertStore(tmp_path / "alerts"))
    monkeypatch.setattr(deps, "_alert_service", service)
    token = pro_token(monkeypatch, tmp_path)

    resp = client.post(
        "/api/alerts",
        json={"symbol": "AAPL", "market": "US", "metric": "PRICE", "condition": "ABOVE", "value": 100.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    rule_id = resp.json()["rule_id"]

    resp = client.get("/api/alerts", headers={"Authorization": f"Bearer {token}"})
    assert len(resp.json()) == 1

    resp = client.delete(f"/api/alerts/{rule_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    resp = client.delete(f"/api/alerts/{rule_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_alerts_validation_422(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.alerts import AlertService, AlertStore

    monkeypatch.setattr(deps, "_alert_service", AlertService(AlertStore(tmp_path / "alerts")))
    token = pro_token(monkeypatch, tmp_path)
    resp = client.post(
        "/api/alerts",
        json={"symbol": "AAPL", "market": "US", "metric": "PRICE", "condition": "ABOVE", "value": -5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_alerts_check_and_notifications(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.alerts import AlertService, AlertStore

    service = AlertService(AlertStore(tmp_path / "alerts"))
    monkeypatch.setattr(deps, "_alert_service", service)
    token = pro_token(monkeypatch, tmp_path)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/api/alerts",
        json={"symbol": "AAPL", "market": "US", "metric": "PRICE", "condition": "ABOVE", "value": 100.0},
        headers=headers,
    )
    resp = client.post("/api/alerts/check", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["triggered"] == 1
    assert "AAPL" in resp.json()["notifications"][0]["message"]

    resp = client.get("/api/alerts/notifications", headers=headers)
    assert len(resp.json()) == 1

    resp = client.post("/api/alerts/notifications/clear", headers=headers)
    assert resp.json()["cleared"] == 1

    resp = client.get("/api/alerts/notifications", headers=headers)
    assert resp.json() == []


def test_alerts_unauth_401(client):
    resp = client.post(
        "/api/alerts",
        json={"symbol": "AAPL", "market": "US", "metric": "PRICE", "condition": "ABOVE", "value": 100.0},
    )
    assert resp.status_code == 401
    resp = client.get("/api/alerts/notifications")
    assert resp.status_code == 401


def test_assistant_confirm(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.ai_assistant import AIAssistantService

    class FakeGen:
        def generate(self, prompt):
            return "```python\nsignals = data['close'] * 0\n```"

    token = pro_token(monkeypatch, tmp_path)
    service = AIAssistantService(FakeGen())
    monkeypatch.setattr(deps, "_assistant_service", service)
    client.post(
        "/api/assistant/chat",
        json={"user_id": "u1", "message": "make strategy"},
        headers={"Authorization": f"Bearer {token}"},
    )
    ok = client.post(
        "/api/assistant/confirm", json={"user_id": "u1", "action": "run backtest with generated strategy"}
    )
    assert ok.status_code == 200
    bad = client.post(
        "/api/assistant/confirm", json={"user_id": "u1", "action": "nope"}
    )
    assert bad.status_code == 409

def test_auth_register_login_me(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.auth_billing import AuthService, UserStore

    monkeypatch.setattr(deps, "_auth_service", AuthService(UserStore(tmp_path / "auth")))
    reg = client.post("/api/auth/register", json={"email": "u@test.com", "password": "password123"})
    assert reg.status_code == 200
    token = reg.json()["token"]
    assert reg.json()["user"]["plan"] == "free"
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "u@test.com"


def test_auth_login_wrong_password(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.auth_billing import AuthService, UserStore

    monkeypatch.setattr(deps, "_auth_service", AuthService(UserStore(tmp_path / "auth")))
    client.post("/api/auth/register", json={"email": "u@test.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "u@test.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_auth_subscribe_upgrades_plan(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.auth_billing import AuthService, UserStore

    monkeypatch.setattr(deps, "_auth_service", AuthService(UserStore(tmp_path / "auth")))
    token = client.post("/api/auth/register", json={"email": "u@test.com", "password": "password123"}).json()["token"]
    sub = client.post("/api/auth/subscribe", json={"plan": "pro"}, headers={"Authorization": f"Bearer {token}"})
    assert sub.status_code == 200
    assert sub.json()["plan"] == "pro"


def test_me_unauth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_journal_add_and_list(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.trading_journal import JournalService, JournalStore

    monkeypatch.setattr(deps, "_journal_service", JournalService(JournalStore(tmp_path / "journal")))
    resp = client.post(
        "/api/journal/entry",
        json={"user_id": "demo", "trade_id": "t1", "note": "good setup", "symbol": "TEST", "pnl": 150.0, "rating": 4},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["note"] == "good setup"
    entries = client.get("/api/journal", params={"user_id": "demo"}).json()
    assert len(entries) == 1
    dele = client.delete(f"/api/journal/{body['entry_id']}", params={"user_id": "demo"})
    assert dele.status_code == 200
    assert client.get("/api/journal", params={"user_id": "demo"}).json() == []


def test_screener_scan(client, fake_provider, tmp_path, monkeypatch):
    from app.api import deps

    rows = client.post("/api/screener/scan", json={"market": "IN", "filters": {"min_price": 100}}).json()
    assert rows["count"] == 1
    assert rows["results"][0]["symbol"] == "TEST"


def test_export_csv(client, fake_provider, tmp_path, monkeypatch):
    from app.api import deps
    from modules.market_data.storage.parquet_store import ParquetStore

    store = ParquetStore(tmp_path)
    store.write("IN", "1d", "TEST", fake_provider._df)
    monkeypatch.setattr(deps, "parquet_store", lambda: store)
    resp = client.get("/api/export/csv", params={"market": "IN", "symbol": "TEST"})
    assert resp.status_code == 200
    assert "close" in resp.text
    assert resp.headers["content-type"].startswith("text/csv")


def test_export_csv_missing_404(client, tmp_path, monkeypatch):
    from app.api import deps
    from modules.market_data.storage.parquet_store import ParquetStore

    monkeypatch.setattr(deps, "parquet_store", lambda: ParquetStore(tmp_path))
    resp = client.get("/api/export/csv", params={"market": "IN", "symbol": "MISSING"})
    assert resp.status_code == 404


def test_bar_timestamp_intraday_includes_time():
    from app.api.market import bar_timestamp

    ts = pd.Timestamp("2024-01-02 09:31")
    assert bar_timestamp(ts, "1m") == "2024-01-02 09:31"
    assert bar_timestamp(ts, "1h") == "2024-01-02 09:31"
    assert bar_timestamp(ts, "1d") == "2024-01-02"


def test_default_range_shrinks_for_intraday():
    from app.api.market import default_range

    assert default_range("1m").days == 7
    assert default_range("1h").days == 60
    assert default_range("1d").days == 730


def test_ohlcv_intraday_format(client):
    resp = client.get("/api/ohlcv/TEST", params={"market": "IN", "interval": "1m"})
    assert resp.status_code == 200
    assert " 00:00" in resp.json()["bars"][0]["date"]


def test_paper_replay(client, tmp_path, monkeypatch):
    from pathlib import Path

    from app.api import deps
    from modules.paper_trading import AccountStore

    monkeypatch.setattr(
        deps, "paper_store", lambda: AccountStore(Path(tmp_path) / "accounts")
    )
    resp = client.post(
        "/api/paper/replay",
        json={
            "user_id": "demo",
            "market": "IN",
            "symbol": "TEST",
            "interval": "1d",
            "start": "2024-01-01",
            "end": "2024-01-10",
            "code": (
                "signals = (data['close'] > data['close'].rolling(3).mean()).astype(int)"
            ),
            "initial_capital": 100000.0,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "TEST"
    assert body["round_trips"] >= 0
