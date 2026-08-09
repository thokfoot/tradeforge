import pandas as pd
import pytest

from modules.ai_agent.cache import TtlCache
from modules.ai_agent.dsl import DslError
from modules.ai_agent.service import AgentService, build_summary
from modules.ai_agent.store import AgentBacktestStore


@pytest.fixture
def df():
    idx = pd.date_range("2024-01-01", periods=120, freq="D")
    close = pd.Series(range(100, 100 + 120), index=idx, dtype=float)
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )


def test_cache_get_miss_then_hit():
    cache = TtlCache(ttl_seconds=60)
    assert cache.get("k") is None
    cache.set("k", "v")
    assert cache.get("k") == "v"


def test_service_parse_falls_back(tmp_path, df):
    store = AgentBacktestStore(tmp_path / "agent")
    service = AgentService(store)
    dsl = service.parse("RELIANCE RSI 30 se neeche aaye toh lele, SL 1%, TP 2%")
    assert dsl["symbol"] == "RELIANCE"


def test_service_run_and_history(tmp_path, df):
    store = AgentBacktestStore(tmp_path / "agent")
    service = AgentService(store)
    out = service.run(
        "u1",
        {
            "intent": "run_backtest",
            "symbol": "TEST",
            "market": "IN",
            "interval": "1d",
            "entry": {"indicator": "RSI", "op": "<", "value": 30},
        },
        lambda symbol, interval, start, end: df,
    )
    assert out["backtest_id"]
    assert isinstance(out["metrics"]["total_trades"], int)
    assert "TEST" in out["summary"]

    history = service.history("u1")
    assert len(history) == 1
    assert history[0]["id"] == out["backtest_id"]
    assert history[0]["symbol"] == "TEST"
    assert service.history("u2") == []


def test_service_review_cached(tmp_path, df):
    store = AgentBacktestStore(tmp_path / "agent")
    service = AgentService(store, reviewer=lambda summary: "Groq review")
    out = service.run(
        "u1",
        {
            "intent": "run_backtest",
            "symbol": "TEST",
            "market": "IN",
            "entry": {"indicator": "RSI", "op": "<", "value": 30},
        },
        lambda symbol, interval, start, end: df,
    )
    first = service.review("u1", out["backtest_id"])
    second = service.review("u1", out["backtest_id"])
    assert first["review"] == "Groq review"
    assert first["cached"] is False
    assert second["cached"] is True


def test_service_review_fallback_rule(tmp_path, df):
    store = AgentBacktestStore(tmp_path / "agent")
    service = AgentService(store)
    out = service.run(
        "u1",
        {
            "intent": "run_backtest",
            "symbol": "TEST",
            "market": "IN",
            "entry": {"indicator": "RSI", "op": "<", "value": 30},
        },
        lambda symbol, interval, start, end: df,
    )
    review = service.review("u1", out["backtest_id"])
    assert review["review"]
    assert isinstance(review["chips"], list)


def test_service_run_unknown_market(tmp_path, df):
    service = AgentService(AgentBacktestStore(tmp_path / "agent"))
    with pytest.raises(DslError):
        service.run(
            "u1",
            {
                "intent": "run_backtest",
                "symbol": "TEST",
                "market": "MOON",
                "entry": {"indicator": "RSI", "op": "<", "value": 30},
            },
            lambda symbol, interval, start, end: df,
        )


def test_service_run_review_intent_rejected(tmp_path, df):
    service = AgentService(AgentBacktestStore(tmp_path / "agent"))
    with pytest.raises(DslError):
        service.run(
            "u1",
            {"intent": "review", "symbol": "TEST"},
            lambda symbol, interval, start, end: df,
        )


def test_build_summary():
    metrics = type(
        "M",
        (),
        {
            "total_trades": 25,
            "win_rate_pct": 60.0,
            "max_drawdown_pct": -8.5,
            "profit_factor": 1.9,
            "total_return_pct": 12.3,
        },
    )()
    text = build_summary("RELIANCE", "1d", metrics, [])
    assert "RELIANCE" in text
    assert "25 trades" in text
