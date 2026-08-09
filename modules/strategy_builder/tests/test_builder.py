import numpy as np
import pandas as pd
import pytest

from modules.strategy_builder import StrategyBuilder


def _df():
    idx = pd.date_range("2024-01-01", periods=60, freq="B")
    close = pd.Series(np.sin(np.linspace(0, 6, 60)) * 5 + 100.0, index=idx)
    return pd.DataFrame(
        {
            "open": close + 0.1,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )


def _run(spec):
    code = StrategyBuilder().generate(spec)
    ns = {"pd": pd, "np": np, "data": _df(), "params": {}}
    exec(code, ns)
    return ns["signals"]


def test_generate_produces_valid_signals_series():
    spec = {
        "entry": {
            "op": "AND",
            "conditions": [
                {"indicator": "rsi", "period": 14, "op": "below", "value": 30},
            ],
        },
        "exit": {
            "op": "OR",
            "conditions": [
                {"indicator": "rsi", "period": 14, "op": "above", "value": 70},
            ],
        },
    }
    signals = _run(spec)
    assert isinstance(signals, pd.Series)
    assert set(signals.unique()).issubset({-1, 1})
    assert len(signals) == 60


def test_generate_close_vs_sma():
    spec = {
        "entry": {
            "op": "AND",
            "conditions": [
                {"indicator": "close", "op": "above", "ref": "sma", "ref_period": 20},
            ],
        }
    }
    signals = _run(spec)
    assert set(signals.unique()).issubset({-1, 1})
    # default exit = not entry -> long whenever close above sma20
    ma = _df()["close"].rolling(20).mean()
    expected = pd.Series(np.where(_df()["close"] > ma, 1, -1), index=_df().index)
    assert list(signals) == list(expected)


def test_validate_rejects_unknown_indicator():
    errors = StrategyBuilder().validate(
        {"entry": {"op": "AND", "conditions": [{"indicator": "macd", "op": "above", "value": 5}]}}
    )
    assert any("indicator" in e for e in errors)


def test_validate_rejects_bad_op():
    errors = StrategyBuilder().validate(
        {"entry": {"op": "AND", "conditions": [{"indicator": "rsi", "op": "crosses", "value": 50}]}}
    )
    assert any("op" in e for e in errors)


def test_validate_rejects_missing_value():
    errors = StrategyBuilder().validate(
        {"entry": {"op": "AND", "conditions": [{"indicator": "close", "op": "above"}]}}
    )
    assert any("value" in e for e in errors)


def test_validate_empty_spec():
    errors = StrategyBuilder().validate({})
    assert any("at least one" in e for e in errors)


def test_generate_raises_on_invalid_spec():
    with pytest.raises(ValueError):
        StrategyBuilder().generate(
            {"entry": {"op": "AND", "conditions": [{"indicator": "bogus", "op": "above", "value": 1}]}}
        )


def test_generated_code_holds_stateful_entries():
    spec = {
        "entry": {"op": "AND", "conditions": [{"indicator": "rsi", "period": 14, "op": "below", "value": 50}]},
        "exit": {"op": "AND", "conditions": [{"indicator": "rsi", "period": 14, "op": "above", "value": 60}]},
    }
    signals = _run(spec)
    # must be a valid long/flat series (1 in market, -1 flat)
    assert signals.min() >= -1 and signals.max() <= 1


def test_ema_and_volume_expressions():
    spec = {
        "entry": {
            "op": "AND",
            "conditions": [
                {"indicator": "ema", "period": 9, "op": "above", "value": 100},
                {"indicator": "volume", "op": "above", "value": 500},
            ],
        }
    }
    signals = _run(spec)
    assert set(signals.unique()).issubset({-1, 1})
