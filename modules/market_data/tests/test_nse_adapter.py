from datetime import date, timedelta

import pandas as pd
import pytest

from modules.market_data.canonical import normalize_bhavcopy, normalize_indices
from modules.market_data.providers.nse_archive import NSEArchiveProvider
from modules.market_data.storage.parquet_store import ParquetStore


def _bhav_for(d: date) -> pd.DataFrame:
    base = d.toordinal() / 1000.0
    return pd.DataFrame(
        {
            "SYMBOL": ["RELIANCE", "TCS"],
            "OPEN_PRICE": [100.0 + base, 50.0 + base],
            "HIGH_PRICE": [110.0 + base, 55.0 + base],
            "LOW_PRICE": [95.0 + base, 48.0 + base],
            "CLOSE_PRICE": [105.0 + base, 52.0 + base],
            "TTL_TRD_QNTY": [1000, 2000],
            "DELIV_QTY": [" 500", " 800"],
            "DELIV_PER": [" 50.0", " 40.0"],
        }
    )


def _index_for(d: date) -> pd.DataFrame:
    base = d.toordinal() / 1000.0
    return pd.DataFrame(
        {
            "Index Name": ["Nifty 50"],
            "Open Index Value": [24000.0 + base],
            "High Index Value": [24100.0 + base],
            "Low Index Value": [23900.0 + base],
            "Closing Index Value": [24050.0 + base],
            "Volume": ["355518193"],
            "P/E": ["20.91"],
            "P/B": ["3.02"],
            "Div Yield": ["1.26"],
        }
    )


@pytest.fixture
def provider(tmp_path) -> NSEArchiveProvider:
    p = NSEArchiveProvider(store=ParquetStore(tmp_path))
    p._fetch_bhavcopy = lambda d: normalize_bhavcopy(_bhav_for(d), d)
    p._fetch_indices = lambda d: normalize_indices(_index_for(d), d)
    p._index_slugs = {"NIFTY50"}
    return p


def test_fetch_ohlcv_merges_days(provider):
    start = pd.Timestamp("2026-08-03")
    end = pd.Timestamp("2026-08-05")
    df = provider.fetch_ohlcv("RELIANCE", "1d", start, end)
    assert len(df) == 3
    assert list(df.index) == sorted(df.index)
    assert df.index.name == "date"
    assert "close" in df.columns


def test_fetch_ohlcv_second_call_uses_store(provider):
    start = pd.Timestamp("2026-08-03")
    end = pd.Timestamp("2026-08-04")
    calls = {"n": 0}
    original = provider._fetch_bhavcopy

    def counted(d):
        calls["n"] += 1
        return original(d)

    provider._fetch_bhavcopy = counted
    provider.fetch_ohlcv("RELIANCE", "1d", start, end)
    first = calls["n"]
    provider.fetch_ohlcv("RELIANCE", "1d", start, end)
    assert calls["n"] == first, "second call must hit local store, not the network"


def test_fetch_ohlcv_rejects_unsupported_interval(provider):
    with pytest.raises(ValueError):
        provider.fetch_ohlcv(
            "RELIANCE", "1m", pd.Timestamp("2026-08-03"), pd.Timestamp("2026-08-04")
        )


def test_fetch_ohlcv_index_symbol_uses_indices(provider):
    start = pd.Timestamp("2026-08-03")
    end = pd.Timestamp("2026-08-04")
    df = provider.fetch_ohlcv("NIFTY50", "1d", start, end)
    assert len(df) == 2
    assert "pe" in df.columns


def test_fetch_quote_returns_latest(provider):
    quote = provider.fetch_quote("RELIANCE")
    assert quote.symbol == "RELIANCE"
    assert quote.price == pytest.approx(105.0 + date(2026, 8, 6).toordinal() / 1000.0, abs=1.0)
    assert quote.timestamp is not None


def test_get_symbols_includes_stocks_and_indices(provider):
    infos = provider.get_symbols(as_of=date(2026, 8, 6))
    kinds = {(i.symbol, i.instrument_type) for i in infos}
    assert ("RELIANCE", "stock") in kinds
    assert ("TCS", "stock") in kinds
    assert ("NIFTY50", "index") in kinds
    assert all(i.market == "IN" for i in infos)


def test_backfill_populates_store(provider, tmp_path):
    stats = provider.backfill(
        ["RELIANCE", "TCS"], "1d", date(2026, 8, 3), date(2026, 8, 5)
    )
    assert stats["RELIANCE"] == 3
    assert stats["TCS"] == 3
    store = ParquetStore(tmp_path)
    assert store.has("IN", "1d", "RELIANCE")
    assert len(store.read("IN", "1d", "TCS")) == 3
