import numpy as np
import pandas as pd
import pytest

from modules.strategy_engine.sandbox import run_code


def _df():
    idx = pd.date_range("2024-01-01", periods=30, freq="B")
    close = pd.Series(range(30), index=idx, dtype=float)
    return pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close, "volume": 1000.0},
        index=idx,
    )


def _ns(code_data=None):
    return {"np": np, "pd": pd, "data": code_data if code_data is not None else _df(), "params": {}}


def test_blocks_pandas_file_read():
    with pytest.raises(Exception):
        run_code("signals = pd.read_csv('/etc/passwd').iloc[:,0]", _ns())


def test_blocks_dataframe_to_csv():
    with pytest.raises(Exception):
        run_code("signals = data['close']\ndata.to_csv('/tmp/out.csv')", _ns())


def test_blocks_dunder_escape():
    with pytest.raises(Exception):
        run_code("signals = ().__class__.__mro__[1].__subclasses__()", _ns())


def test_blocks_getattr_builtin():
    with pytest.raises(Exception):
        run_code("signals = getattr(__builtins__, 'eval')('1+1')", _ns())


def test_blocks_exec_and_eval():
    with pytest.raises(Exception):
        run_code("exec('x = 1')\nsignals = data['close']", _ns())
    with pytest.raises(Exception):
        run_code("signals = eval('1+1')", _ns())


def test_blocks_import_from():
    with pytest.raises(NameError):
        run_code("from os import system\nsignals = data['close']", _ns())


def test_legit_pandas_strategy_still_works():
    code = (
        "sma = data['close'].rolling(5).mean()\n"
        "signals = (data['close'] > sma).astype(int)"
    )
    ns = run_code(code, _ns())
    assert isinstance(ns["signals"], pd.Series)


def test_params_still_available():
    code = "period = params.get('fast', 5)\nsignals = (data['close'] > data['close'].rolling(period).mean()).astype(int)"
    ns = run_code(code, _ns())
    assert isinstance(ns["signals"], pd.Series)


def test_timeout_kills_runaway_strategy():
    with pytest.raises(TimeoutError):
        run_code("while True:\n    pass", _ns(), timeout=0.5)
