import pandas as pd

from modules.backtest_engine.simulator import order_charges, simulate
from modules.shared.contracts import CostModel, DataBundle, StrategyConfig, SymbolInfo


def _bundle() -> DataBundle:
    idx = pd.DatetimeIndex(
        ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
        name="date",
    )
    df = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104],
            "high": [100, 101, 102, 103, 104],
            "low": [100, 101, 102, 103, 104],
            "close": [100, 101, 102, 103, 104],
            "volume": [1, 1, 1, 1, 1],
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


def _cfg() -> StrategyConfig:
    return StrategyConfig(
        initial_capital=1000.0,
        position_sizing="fixed",
        position_size=9,
    )


def test_golden_no_cost_scenario():
    bundle = _bundle()
    signals = pd.Series([0, 1, 1, 0, 0], index=bundle.df.index)
    equity, trades = simulate(bundle, signals, CostModel(), _cfg())
    assert equity.tolist() == [1000.0, 1000.0, 1000.0, 1009.0, 1018.0]
    assert len(trades) == 1
    assert trades[0].pnl == 18.0
    assert trades[0].side == "SELL"
    assert trades[0].symbol == "TEST"


def test_execution_uses_next_bar_open_not_signal_bar():
    bundle = _bundle()
    signals = pd.Series([1, 1, 1, 1, 1], index=bundle.df.index)
    equity, trades = simulate(bundle, signals, CostModel(), _cfg())
    assert len(trades) == 0
    assert equity.iloc[0] == 1000.0, "no signal before first bar, must stay flat"
    assert equity.iloc[1] == 1000.0, "entered at open[1]=101, close[1]=101, no pnl yet"
    assert equity.iloc[2] == 1009.0, "9 shares held into close[2]=102"


def test_always_flat():
    bundle = _bundle()
    signals = pd.Series([0, 0, 0, 0, 0], index=bundle.df.index)
    equity, trades = simulate(bundle, signals, CostModel(), _cfg())
    assert len(trades) == 0
    assert equity.tolist() == [1000.0] * 5


def test_order_charges_stt_only_on_sell():
    c = CostModel(brokerage=20.0, stt_pct=0.001)
    assert order_charges(c, 100000.0, "BUY") == 20.0
    assert order_charges(c, 100000.0, "SELL") == 120.0


def test_slippage_reduces_sell_proceeds():
    c = CostModel(slippage_pct=0.01)
    bundle = _bundle()
    signals = pd.Series([0, 1, 1, 0, 0], index=bundle.df.index)
    equity, trades = simulate(bundle, signals, CostModel(slippage_pct=0.0), _cfg())
    equity_slip, trades_slip = simulate(bundle, signals, c, _cfg())
    assert trades_slip[0].pnl < trades[0].pnl
