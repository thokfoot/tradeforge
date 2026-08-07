import numpy as np
import pandas as pd

from modules.screener import ScreenerService
from modules.shared.contracts import ScreenerRow


def make_series(n: int = 250, start: float = 100.0, growth: float = 0.0):
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    rng = np.random.default_rng(7)
    noise = np.cumsum(rng.normal(0, 0.3, n))
    trend = start * (1 + growth) ** np.arange(n)
    close = pd.Series(trend + noise, index=idx)
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": np.full(n, 10_000.0),
        },
        index=idx,
    )


def loader(symbol: str) -> pd.DataFrame:
    if symbol == "RISER":
        return make_series(growth=0.002)
    if symbol == "FALLER":
        return make_series(growth=-0.002)
    if symbol == "SHORT":
        return make_series(n=1)
    return make_series()


def test_scan_returns_rows():
    service = ScreenerService(loader)
    rows = service.scan(["RISER", "FALLER", "FLAT", "SHORT"])
    assert all(isinstance(r, ScreenerRow) for r in rows)
    assert len(rows) == 3


def test_price_filter():
    service = ScreenerService(loader)
    rows = service.scan(["RISER", "FALLER"], {"min_price": 150})
    assert [r.symbol for r in rows] == ["RISER"]


def test_sort_by_change_desc():
    service = ScreenerService(loader)
    rows = service.scan(["FALLER", "RISER"], {"sort_by": "change_1m_pct"})
    assert rows[0].symbol == "RISER"
    assert rows[1].symbol == "FALLER"


def test_bool_filter_above_sma():
    service = ScreenerService(loader)
    rows = service.scan(["RISER", "FALLER"], {"above_sma_200": True})
    assert [r.symbol for r in rows] == ["RISER"]


def test_single_bar_series_skipped():
    service = ScreenerService(loader)
    rows = service.scan(["SHORT"], {})
    assert rows == []


def test_bad_symbol_skipped():
    service = ScreenerService(lambda s: (_ for _ in ()).throw(ValueError("boom")))
    assert service.scan(["X"]) == []


def test_short_series_metrics_none():
    service = ScreenerService(loader)
    row = service._metrics("PARTIAL", make_series(n=30))
    assert row.change_3m_pct is None
    assert row.above_sma_200 is None
    assert row.change_1d_pct is not None


def test_indicators_computed():
    service = ScreenerService(loader)
    row = service._metrics("RISER", make_series(n=250, growth=0.002))
    assert row.rsi_14 is not None and row.rsi_14 > 50
    assert row.bb_position is not None
    assert row.vol_ratio_20 is not None
    assert row.above_sma_20 is True
    assert row.macd_above_signal is not None


def test_rsi_filter_extreme():
    service = ScreenerService(loader)
    assert service.scan(["RISER", "FALLER"], {"min_rsi": 200}) == []
    assert service.scan(["RISER", "FALLER"], {"max_rsi": 0}) == []


def test_bb_filter():
    service = ScreenerService(loader)
    assert service.scan(["RISER"], {"min_bb_position": 10}) == []
    assert [r.symbol for r in service.scan(["RISER"], {"min_bb_position": -10})] == ["RISER"]


def test_vol_ratio_filter():
    service = ScreenerService(loader)
    assert [r.symbol for r in service.scan(["RISER"], {"min_vol_ratio": 0.5})] == ["RISER"]
    assert service.scan(["RISER"], {"min_vol_ratio": 5}) == []


def test_sma20_filter():
    service = ScreenerService(loader)
    rows = service.scan(["RISER", "FALLER"], {"above_sma_20": True})
    assert "RISER" in [r.symbol for r in rows]


def test_sort_by_rsi():
    service = ScreenerService(loader)
    rows = service.scan(["FALLER", "RISER"], {"sort_by": "rsi_14"})
    assert rows[0].symbol == "RISER"


def test_macd_above_signal_short_series_none():
    service = ScreenerService(loader)
    row = service._metrics("PARTIAL", make_series(n=30))
    assert row.macd_above_signal is None
    assert row.rsi_14 is not None
