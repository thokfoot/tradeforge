import json

import pandas as pd
import pytest

from modules.market_data.providers.binance import BinanceProvider, klines_to_df


def _row(ms, o=1.0, h=2.0, lo=0.5, c=1.5, v=100.0):
    return [ms, o, h, lo, c, v, ms + 60_000, 0.0, 1, 0.0, 0.0, 0.0]


def test_klines_to_df_maps_fields():
    rows = [_row(1_000_000), _row(1_100_000, c=1.6)]
    out = klines_to_df(rows)
    assert list(out.columns) == ["open", "high", "low", "close", "volume"]
    assert out["close"].tolist() == [1.5, 1.6]
    assert out["volume"].tolist() == [100.0, 100.0]
    assert out.index.name == "date"
    assert out.index.is_monotonic_increasing


def test_klines_to_df_empty():
    assert klines_to_df([]).empty


class _FakeClient:
    def __init__(self, klines=None, symbols=None):
        self.klines = list(klines or [])
        self.symbols = symbols or []
        self.requests = []

    def get(self, url, params=None):
        self.requests.append((url, params))
        if "klines" in url:
            payload = self.klines.pop(0) if self.klines else []
        else:
            payload = {"symbols": self.symbols}
        return _FakeResponse(json.dumps(payload))


class _FakeResponse:
    def __init__(self, text):
        self._text = text

    def raise_for_status(self):
        pass

    def json(self):
        return json.loads(self._text)


def test_fetch_ohlcv_paginates(provider_factory):
    page1 = [_row(i) for i in range(0, 3_600_000, 1_000_000)]
    page2 = [_row(3_600_000, c=9.0)]
    client = _FakeClient(klines=[page1, page2])
    provider = provider_factory(client)
    df = provider.fetch_ohlcv(
        "BTCUSDT", "1h", pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-01")
    )
    assert len(df) == 5
    assert df["close"].iloc[-1] == 9.0
    assert len(client.requests) >= 2
    assert client.requests[1][1]["startTime"] == 3_000_001


def test_get_symbols_filters(provider_factory):
    client = _FakeClient(
        symbols=[
            {"symbol": "BTCUSDT", "status": "TRADING", "baseAsset": "BTC", "quoteAsset": "USDT"},
            {"symbol": "XXBTBTC", "status": "TRADING", "baseAsset": "XXBT", "quoteAsset": "BTC"},
            {"symbol": "ETHUSDT", "status": "BREAK", "baseAsset": "ETH", "quoteAsset": "USDT"},
            {"symbol": "SOLUSDT", "status": "TRADING", "baseAsset": "SOL", "quoteAsset": "USDT"},
        ]
    )
    infos = provider_factory(client).get_symbols()
    assert [i.symbol for i in infos] == ["BTCUSDT", "SOLUSDT"]


def test_fetch_quote(provider_factory):
    client = _FakeClient(klines=[[[1234, 100, 110, 99, 105, 500, 0, 0, 0, 0, 0, 0]]])
    quote = provider_factory(client).fetch_quote("BTCUSDT")
    assert quote.price == 105.0
    assert quote.volume == 500.0


@pytest.fixture
def provider_factory():
    def _make(client):
        return BinanceProvider(client=client)

    return _make
