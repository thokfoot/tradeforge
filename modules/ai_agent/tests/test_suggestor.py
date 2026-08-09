from modules.ai_agent.rules.suggestor import suggest


def test_suggest_low_win_rate():
    chips = suggest({"win_rate_pct": 20, "total_trades": 30, "max_drawdown_pct": -10, "profit_factor": 1.5})
    assert chips
    assert any("SL" in chip for chip in chips)


def test_suggest_bad_profit_factor():
    chips = suggest({"win_rate_pct": 50, "total_trades": 30, "max_drawdown_pct": -10, "profit_factor": 1.0})
    assert any("Profit factor" in chip for chip in chips)


def test_suggest_low_samples():
    chips = suggest({"win_rate_pct": 50, "total_trades": 5, "max_drawdown_pct": -5, "profit_factor": 2.0})
    assert any("trades" in chip for chip in chips)


def test_suggest_max_three():
    chips = suggest(
        {
            "win_rate_pct": 20,
            "total_trades": 5,
            "max_drawdown_pct": -40,
            "profit_factor": 0.8,
            "loss_hour": 15,
        }
    )
    assert len(chips) <= 3


def test_suggest_empty_metrics():
    assert suggest({}) == []
    assert suggest({"win_rate_pct": 50, "total_trades": 50, "max_drawdown_pct": -5, "profit_factor": 2.0}) == []
