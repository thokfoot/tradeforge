import pandas as pd
import pytest

from modules.backtest_engine import EventDrivenEngine
from modules.shared.contracts import (
    BacktestResult,
    CostModel,
    DataBundle,
    Strategy,
    StrategyConfig,
    SymbolInfo,
)


def _bundle() -> DataBundle:
    idx = pd.date_range("2024-01-01", periods=60, freq="B")
    close = pd.Series(range(100, 160), index=idx, dtype=float)
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
    sym = SymbolInfo(
        symbol="TEST",
        market="IN",
        exchange="NSE",
        name="Test",
        currency="INR",
        instrument_type="stock",
    )
    return DataBundle(symbol=sym, interval="1d", df=df, source="test", data_version="v1")


def _strategy(code: str) -> Strategy:
    return Strategy(
        id="s1",
        version="1.0",
        author_user_id="u1",
        code=code,
        params={"fast": 5},
        config=StrategyConfig(initial_capital=100000.0),
    )


def test_run_returns_result():
    code = (
        "signals = (data['close'] > data['close'].rolling(5).mean()).astype(int)"
    )
    result = EventDrivenEngine().run(_strategy(code), _bundle(), CostModel())
    assert isinstance(result, BacktestResult)
    assert result.symbol == "TEST"
    assert result.strategy_id == "s1"
    assert len(result.equity_curve) == 60
    assert result.metrics.total_trades >= 0
    assert result.run_hash


def test_run_rejects_missing_signals_variable():
    with pytest.raises(ValueError):
        EventDrivenEngine().run(_strategy("x = 1"), _bundle(), CostModel())


def test_run_rejects_empty_data():
    bundle = _bundle()
    empty = DataBundle(
        symbol=bundle.symbol,
        interval=bundle.interval,
        df=bundle.df.iloc[0:0],
        source=bundle.source,
        data_version=bundle.data_version,
    )
    with pytest.raises(ValueError):
        EventDrivenEngine().run(_strategy("signals = data['close']"), empty, CostModel())


def test_reproducible_hash_is_stable():
    engine = EventDrivenEngine()
    s = _strategy("signals = data['close'] * 0")
    assert engine.reproducible_hash(s, "v1", s.params) == engine.reproducible_hash(s, "v1", s.params)
    assert engine.reproducible_hash(s, "v1", s.params) != engine.reproducible_hash(s, "v2", s.params)


def test_engine_implements_contract():
    from modules.shared.contracts.interfaces import BacktestEngine

    assert isinstance(EventDrivenEngine(), BacktestEngine)
