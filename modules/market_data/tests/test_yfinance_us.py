import pandas as pd

from modules.market_data.providers.yfinance_us import YFinanceProvider, to_canonical


def _yf_frame():
    idx = pd.DatetimeIndex(
        ["2026-08-04 00:00:00+00:00", "2026-08-05 00:00:00+00:00"]
    )
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [110.0, 111.0],
            "Low": [90.0, 91.0],
            "Close": [105.0, 106.0],
            "Volume": [1000, 1100],
        },
        index=idx,
    )


def test_to_canonical_maps_and_drops_tz():
    out = to_canonical(_yf_frame())
    assert list(out.columns) == ["open", "high", "low", "close", "volume"]
    assert out["close"].tolist() == [105.0, 106.0]
    assert out["volume"].tolist() == [1000, 1100]
    assert not isinstance(out.index.tz, type(None)) is False
    assert str(out.index[0]) == "2026-08-04 00:00:00"


def test_to_canonical_empty():
    out = to_canonical(pd.DataFrame())
    assert out.empty
    assert out.index.name == "date"


def test_provider_market_defaults():
    p = YFinanceProvider()
    assert p.market == "US"
    assert p.currency == "USD"
    assert p.supported_intervals == {"1d", "1h", "1m"}


def test_get_symbols_returns_popular_list():
    infos = YFinanceProvider().get_symbols()
    assert len(infos) >= 40
    symbols = {i.symbol for i in infos}
    assert "AAPL" in symbols and "SPY" in symbols
    kinds = {i.symbol: i.instrument_type for i in infos}
    assert kinds["SPY"] == "etf"
    assert all(i.market == "US" for i in infos)
