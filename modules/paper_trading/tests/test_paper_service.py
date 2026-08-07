import pytest

from modules.paper_trading import AccountStore, PaperTraderService, replay_trades
from modules.shared.contracts.interfaces import PaperTrader


@pytest.fixture
def service(tmp_path):
    store = AccountStore(tmp_path / "accounts")
    return PaperTraderService(store=store, pricer=lambda symbol: 100.0)


def test_implements_contract(service):
    assert isinstance(service, PaperTrader)


def test_market_buy_and_sell_round_trip(service):
    buy = service.place_order("u1", "AAPL", "BUY", 10, "MARKET")
    assert buy.status == "FILLED"
    assert buy.filled_price == 100.0
    pos = service.positions("u1")
    assert len(pos) == 1
    assert pos[0].symbol == "AAPL"
    assert pos[0].qty == 10
    assert pos[0].avg_price == 100.0
    assert pos[0].unrealized_pnl == 0.0

    sell = service.place_order("u1", "AAPL", "SELL", 10, "MARKET")
    assert sell.status == "FILLED"
    assert len(service.positions("u1")) == 0
    trades = service.history("u1")
    assert len(trades) == 1
    assert trades[0].pnl == 0.0


def test_insufficient_funds_rejects(service):
    order = service.place_order("u1", "AAPL", "BUY", 2000, "MARKET")
    assert order.status == "REJECTED"


def test_insufficient_position_rejects(service):
    order = service.place_order("u1", "AAPL", "SELL", 5, "MARKET")
    assert order.status == "REJECTED"


def test_negative_qty_rejects(service):
    order = service.place_order("u1", "AAPL", "BUY", -1, "MARKET")
    assert order.status == "REJECTED"


def test_marketable_limit_buy_fills_at_limit(service):
    order = service.place_order("u1", "AAPL", "BUY", 10, "LIMIT", price=105.0)
    assert order.status == "FILLED"
    assert order.filled_price == 105.0


def test_non_marketable_limit_stays_open(service):
    order = service.place_order("u1", "AAPL", "BUY", 10, "LIMIT", price=95.0)
    assert order.status == "OPEN"


def test_average_price_on_add(service):
    service.place_order("u1", "AAPL", "BUY", 10, "MARKET")
    service.place_order("u1", "AAPL", "BUY", 10, "LIMIT", price=110.0)
    pos = service.positions("u1")[0]
    assert pos.qty == 20
    assert pos.avg_price == 105.0


def test_reset_account(service):
    service.place_order("u1", "AAPL", "BUY", 10, "MARKET")
    account = service.reset_account("u1")
    assert account.balance == 100000.0
    assert account.positions == []
    assert len(service.positions("u1")) == 0


def test_account_equity(service):
    account = service.account("u1")
    assert account.balance == 100000.0
    service.place_order("u1", "AAPL", "BUY", 10, "MARKET")
    assert service.account("u1").equity == 100000.0


def test_parity_score_is_win_rate(service):
    assert service.parity_score("u1", "s1") == 0.0
    service.place_order("u1", "AAPL", "BUY", 10, "MARKET")
    assert service.parity_score("u1", "s1") == 0.0


def test_persistence(tmp_path):
    store = AccountStore(tmp_path / "accounts")
    svc = PaperTraderService(store=store, pricer=lambda s: 100.0)
    svc.place_order("u1", "AAPL", "BUY", 10, "MARKET")
    reloaded_store = AccountStore(tmp_path / "accounts")
    reloaded = PaperTraderService(store=reloaded_store, pricer=lambda s: 100.0)
    assert len(reloaded.positions("u1")) == 1
    assert reloaded.positions("u1")[0].qty == 10


def test_reset_account_with_capital(tmp_path):
    store = AccountStore(tmp_path / "accounts")
    svc = PaperTraderService(store=store, pricer=lambda s: 100.0)
    account = svc.reset_account("u1", 50000.0)
    assert account.balance == 50000.0


def test_replay_trades_round_trips(tmp_path):
    store = AccountStore(tmp_path / "accounts")
    fills = [
        ("AAPL", "BUY", 10, 100.0),
        ("AAPL", "SELL", 10, 110.0),
        ("MSFT", "BUY", 5, 200.0),
        ("MSFT", "SELL", 5, 210.0),
    ]
    trades = replay_trades(store, "u1", fills)
    assert len(trades) == 2
    assert all(t.pnl > 0 for t in trades)
    assert sum(t.pnl for t in trades) == 150.0
    assert len(PaperTraderService(store=store, pricer=lambda s: 100.0).positions("u1")) == 0


def test_replay_trades_respects_balance(tmp_path):
    store = AccountStore(tmp_path / "accounts")
    with pytest.raises(ValueError):
        replay_trades(
            store,
            "u1",
            [("AAPL", "BUY", 2000, 100.0)],
        )
