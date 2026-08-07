import numpy as np
import pandas as pd
import pytest

from modules.shared.contracts import Strategy, StrategyConfig
from modules.strategy_engine import StrategyService, StrategyStore, run_code


def _strategy(code: str, strategy_id: str = "s1") -> Strategy:
    return Strategy(
        id=strategy_id,
        version="",
        author_user_id="u1",
        code=code,
        params={"fast": 5},
        config=StrategyConfig(),
    )


def test_sandbox_runs_valid_code():
    ns = run_code(
        "signals = (data['close'] > data['close'].rolling(5).mean()).astype(int)",
        {"np": np, "pd": pd, "data": _df(), "params": {}},
    )
    assert isinstance(ns["signals"], pd.Series)


def _df():
    idx = pd.date_range("2024-01-01", periods=30, freq="B")
    close = pd.Series(range(30), index=idx, dtype=float)
    return pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close, "volume": 1000.0},
        index=idx,
    )


def test_sandbox_blocks_open():
    with pytest.raises(NameError):
        run_code("f = open('x')", {"np": np, "pd": pd, "data": _df(), "params": {}})


def test_sandbox_blocks_import():
    with pytest.raises((NameError, ImportError)):
        run_code("import os", {"np": np, "pd": pd, "data": _df(), "params": {}})


def test_sandbox_timeout():
    with pytest.raises(TimeoutError):
        run_code("while True:\n    pass", {"np": np, "pd": pd, "data": _df(), "params": {}}, timeout=0.5)


def test_validate_ok(tmp_path):
    service = StrategyService(StrategyStore(tmp_path))
    result = service.validate(_strategy("signals = data['close'] * 0"))
    assert result.ok is True


def test_validate_rejects_missing_signals(tmp_path):
    service = StrategyService(StrategyStore(tmp_path))
    result = service.validate(_strategy("x = 1"))
    assert result.ok is False
    assert "signals" in result.errors[0]


def test_validate_rejects_syntax_error(tmp_path):
    service = StrategyService(StrategyStore(tmp_path))
    result = service.validate(_strategy("signals = ("))
    assert result.ok is False


def test_save_assigns_version_and_lists(tmp_path):
    service = StrategyService(StrategyStore(tmp_path))
    saved = service.save(_strategy("signals = data['close'] * 0"))
    assert saved.version == "v1"
    service.save(_strategy("signals = data['close'] * 0"))
    assert service.list_versions("s1") == ["v1", "v2"]


def test_save_rejects_invalid(tmp_path):
    service = StrategyService(StrategyStore(tmp_path))
    with pytest.raises(ValueError):
        service.save(_strategy("x = 1"))


def test_service_implements_contract(tmp_path):
    from modules.shared.contracts.interfaces import StrategyService as Contract

    assert isinstance(StrategyService(StrategyStore(tmp_path)), Contract)
