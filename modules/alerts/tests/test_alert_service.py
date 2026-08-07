import types
from datetime import datetime, timedelta

import pandas as pd
import pytest

from modules.alerts import AlertService, AlertStore
from modules.shared.contracts.interfaces import AlertService as AlertServiceProtocol


class FakeProvider:
    def __init__(self, quote: float, close: pd.Series | None = None):
        self._quote = quote
        self._close = close

    def fetch_quote(self, symbol):
        return types.SimpleNamespace(price=self._quote)

    def fetch_ohlcv(self, symbol, interval, start, end):
        if self._close is None:
            raise AssertionError("no ohlcv configured")
        return pd.DataFrame({"close": self._close})


@pytest.fixture
def service(tmp_path):
    return AlertService(AlertStore(tmp_path / "alerts"))


def test_implements_contract(service):
    assert isinstance(service, AlertServiceProtocol)


def test_create_and_list(service):
    rule = service.create_rule("u1", "AAPL", "US", "PRICE", "ABOVE", 200.0)
    assert rule.active is True
    assert rule.user_id == "u1"
    listed = service.list_rules("u1")
    assert len(listed) == 1
    assert listed[0].rule_id == rule.rule_id


def test_create_validation(service):
    with pytest.raises(ValueError):
        service.create_rule("u1", "AAPL", "US", "P/E", "ABOVE", 10)
    with pytest.raises(ValueError):
        service.create_rule("u1", "AAPL", "US", "PRICE", "AROUND", 10)
    with pytest.raises(ValueError):
        service.create_rule("u1", "AAPL", "US", "PRICE", "ABOVE", -1)


def test_delete_rule(service):
    rule = service.create_rule("u1", "AAPL", "US", "PRICE", "ABOVE", 200.0)
    assert service.delete_rule("u1", rule.rule_id) is True
    assert service.delete_rule("u1", rule.rule_id) is False
    assert service.list_rules("u1") == []


def test_price_alert_triggers_and_deactivates(service):
    rule = service.create_rule("u1", "AAPL", "US", "PRICE", "ABOVE", 100.0)
    triggered = service.check_user("u1", lambda market: FakeProvider(102.5))
    assert len(triggered) == 1
    assert "AAPL" in triggered[0].message
    assert service.list_rules("u1")[0].active is False
    notifs = service.notifications("u1")
    assert len(notifs) == 1
    assert notifs[0].rule_id == rule.rule_id


def test_price_alert_not_triggered(service):
    service.create_rule("u1", "AAPL", "US", "PRICE", "ABOVE", 200.0)
    assert service.check_user("u1", lambda market: FakeProvider(102.5)) == []


def test_rule_fires_once_only(service):
    service.create_rule("u1", "AAPL", "US", "PRICE", "ABOVE", 100.0)
    service.check_user("u1", lambda market: FakeProvider(102.5))
    service.check_user("u1", lambda market: FakeProvider(102.5))
    assert len(service.notifications("u1")) == 1


def test_rsi_alert(service):
    rising = pd.Series(range(1, 40), dtype=float)
    service.create_rule("u1", "AAPL", "US", "RSI", "ABOVE", 70.0)
    triggered = service.check_user("u1", lambda market: FakeProvider(0, rising))
    assert len(triggered) == 1


def test_provider_error_skips_rule(service):
    service.create_rule("u1", "AAPL", "US", "PRICE", "ABOVE", 100.0)

    class Boom:
        def fetch_quote(self, symbol):
            raise RuntimeError("network down")

    assert service.check_user("u1", lambda market: Boom()) == []
    assert service.list_rules("u1")[0].active is True


def test_check_all_multi_user(tmp_path):
    svc = AlertService(AlertStore(tmp_path / "alerts"))
    svc.create_rule("u1", "AAPL", "US", "PRICE", "ABOVE", 100.0)
    svc.create_rule("u2", "AAPL", "US", "PRICE", "ABOVE", 100.0)
    triggered = svc.check_all(lambda market: FakeProvider(102.5))
    assert len(triggered) == 2


def test_clear_notifications(service):
    service.create_rule("u1", "AAPL", "US", "PRICE", "ABOVE", 100.0)
    service.check_user("u1", lambda market: FakeProvider(102.5))
    assert service.clear_notifications("u1") == 1
    assert service.notifications("u1") == []
