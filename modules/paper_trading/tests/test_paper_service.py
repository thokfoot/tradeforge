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


def test_stop_buy_triggered_fills_at_market(service):
    order = service.place_order("u1", "AAPL", "BUY", 10, "STOP", price=95.0)
    assert order.status == "FILLED"
    assert order.filled_price == 100.0


def test_stop_buy_not_triggered_stays_open(service):
    order = service.place_order("u1", "AAPL", "BUY", 10, "STOP", price=105.0)
    assert order.status == "OPEN"


def test_sl_market_triggered_fills(service):
    service.place_order("u1", "AAPL", "BUY", 10, "MARKET")
    order = service.place_order("u1", "AAPL", "SELL", 10, "SL-M", price=105.0)
    assert order.status == "FILLED"
    assert len(service.positions("u1")) == 0


def test_stop_limit_triggered_marketable_fills_at_market(service):
    order = service.place_order(
        "u1", "AAPL", "BUY", 10, "STOP_LIMIT", stop_price=95.0, price=102.0
    )
    assert order.status == "FILLED"
    assert order.filled_price == 100.0


def test_stop_limit_triggered_non_marketable_fills_at_limit(service):
    order = service.place_order(
        "u1", "AAPL", "BUY", 10, "STOP_LIMIT", stop_price=95.0, price=99.0
    )
    assert order.status == "FILLED"
    assert order.filled_price == 99.0


def test_stop_limit_not_triggered_stays_open(service):
    order = service.place_order(
        "u1", "AAPL", "BUY", 10, "STOP_LIMIT", stop_price=105.0, price=110.0
    )
    assert order.status == "OPEN"


def test_bracket_market_attaches_sl_tp(service):
    order = service.place_order(
        "u1", "AAPL", "BUY", 10, "BRACKET", sl=95.0, tp=110.0
    )
    assert order.status == "FILLED"
    pos = service.positions("u1")[0]
    assert pos.sl == 95.0
    assert pos.tp == 110.0


def test_bracket_limit_entry_not_marketable_stays_open(service):
    order = service.place_order(
        "u1", "AAPL", "BUY", 10, "BRACKET", price=95.0, sl=90.0, tp=110.0
    )
    assert order.status == "OPEN"
    assert service.positions("u1") == []


def test_check_exits_hits_stop_loss(service):
    service.place_order("u1", "AAPL", "BUY", 10, "BRACKET", sl=95.0, tp=110.0)
    exits = service.check_exits("u1", {"AAPL": 94.0})
    assert len(exits) == 1
    assert exits[0].side == "SELL"
    assert exits[0].status == "FILLED"
    assert service.positions("u1") == []


def test_check_exits_hits_take_profit(service):
    service.place_order("u1", "AAPL", "BUY", 10, "BRACKET", sl=95.0, tp=110.0)
    exits = service.check_exits("u1", {"AAPL": 111.0})
    assert len(exits) == 1
    assert service.positions("u1") == []


def test_check_exits_ignores_untouched_levels(service):
    service.place_order("u1", "AAPL", "BUY", 10, "BRACKET", sl=95.0, tp=110.0)
    exits = service.check_exits("u1", {"AAPL": 100.0})
    assert exits == []
    assert len(service.positions("u1")) == 1


def test_check_exits_ignores_position_without_sl_tp(service):
    service.place_order("u1", "AAPL", "BUY", 10, "MARKET")
    assert service.check_exits("u1", {"AAPL": 50.0}) == []
    assert len(service.positions("u1")) == 1


def test_sl_tp_persist_across_reload(tmp_path):
    store = AccountStore(tmp_path / "accounts")
    svc = PaperTraderService(store=store, pricer=lambda s: 100.0)
    svc.place_order("u1", "AAPL", "BUY", 10, "BRACKET", sl=95.0, tp=110.0)
    reloaded = PaperTraderService(
        store=AccountStore(tmp_path / "accounts"), pricer=lambda s: 100.0
    )
    pos = reloaded.positions("u1")[0]
    assert pos.sl == 95.0
    assert pos.tp == 110.0


def test_set_levels_updates_position(service):
    service.place_order("u1", "AAPL", "BUY", 10, "BRACKET", sl=95.0, tp=110.0)
    pos = service.set_levels("u1", "AAPL", sl=90.0, tp=115.0)
    assert pos is not None
    assert pos.sl == 90.0
    assert pos.tp == 115.0
    assert service.positions("u1")[0].sl == 90.0
    assert service.positions("u1")[0].tp == 115.0
    assert service.positions("u1")[0].unrealized_pnl == 0.0


def test_set_levels_clears_both(service):
    service.place_order("u1", "AAPL", "BUY", 10, "BRACKET", sl=95.0, tp=110.0)
    pos = service.set_levels("u1", "AAPL", sl=None, tp=None)
    assert pos is not None
    assert pos.sl is None and pos.tp is None


def test_set_levels_no_position_returns_none(service):
    assert service.set_levels("u1", "AAPL", sl=90.0, tp=110.0) is None


def test_set_levels_persists_across_reload(tmp_path):
    store = AccountStore(tmp_path / "accounts")
    svc = PaperTraderService(store=store, pricer=lambda s: 100.0)
    svc.place_order("u1", "AAPL", "BUY", 10, "BRACKET", sl=95.0, tp=110.0)
    svc.set_levels("u1", "AAPL", sl=88.0, tp=118.0)
    reloaded = PaperTraderService(
        store=AccountStore(tmp_path / "accounts"), pricer=lambda s: 100.0
    )
    pos = reloaded.positions("u1")[0]
    assert pos.sl == 88.0
    assert pos.tp == 118.0


def test_updated_levels_trigger_exits(service):
    service.place_order("u1", "AAPL", "BUY", 10, "BRACKET", sl=95.0, tp=110.0)
    service.set_levels("u1", "AAPL", sl=99.0, tp=None)
    exits = service.check_exits("u1", {"AAPL": 98.0})
    assert len(exits) == 1
    assert service.positions("u1") == []
