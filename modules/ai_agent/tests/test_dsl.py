import pytest

from modules.ai_agent.dsl import (
    DslError,
    heuristic_parse,
    plan_text,
    to_builder_spec,
    validate_dsl,
)


def test_heuristic_parse_hindi_buy():
    dsl = heuristic_parse("RELIANCE RSI 30 se neeche aaye toh buy kar le, SL 1%, TP 2%")
    assert dsl["intent"] == "run_backtest"
    assert dsl["symbol"] == "RELIANCE"
    assert dsl["entry"] == {"indicator": "RSI", "op": "<", "value": 30.0}
    assert dsl["sl"] == 1.0
    assert dsl["tp"] == 2.0


def test_heuristic_parse_review():
    dsl = heuristic_parse("AAPL ka backtest review karo")
    assert dsl["intent"] == "review"
    assert dsl["symbol"] == "AAPL"


def test_heuristic_parse_english_above():
    dsl = heuristic_parse("Buy TSLA when RSI is above 55, stop loss 5")
    assert dsl["symbol"] == "TSLA"
    assert dsl["entry"]["op"] == ">"
    assert dsl["entry"]["value"] == 55.0
    assert dsl["sl"] == 5.0


def test_heuristic_parse_defaults():
    dsl = heuristic_parse("banao ek strategy")
    assert dsl["symbol"] == "RELIANCE"
    assert dsl["entry"]["indicator"] == "RSI"
    assert dsl["entry"]["value"] == 30.0


def test_validate_dsl_rejects_bad_intent():
    with pytest.raises(DslError):
        validate_dsl({"intent": "nope", "symbol": "RELIANCE"})


def test_validate_dsl_rejects_bad_indicator():
    with pytest.raises(DslError):
        validate_dsl(
            {
                "intent": "run_backtest",
                "symbol": "RELIANCE",
                "entry": {"indicator": "MACD", "op": "<", "value": 1},
            }
        )


def test_validate_dsl_ok():
    validate_dsl(
        {
            "intent": "run_backtest",
            "symbol": "RELIANCE",
            "entry": {"indicator": "RSI", "op": "<", "value": 30},
            "sl": 1.0,
            "tp": 2.0,
        }
    )


def test_to_builder_spec():
    spec = to_builder_spec(
        {
            "intent": "run_backtest",
            "symbol": "RELIANCE",
            "entry": {"indicator": "RSI", "op": "below", "value": 30},
        }
    )
    assert spec["entry"]["conditions"][0] == {
        "indicator": "rsi",
        "op": "below",
        "value": 30.0,
        "period": 14,
    }


def test_plan_text_includes_sl_tp():
    text = plan_text(
        {
            "intent": "run_backtest",
            "symbol": "reliance",
            "entry": {"indicator": "RSI", "op": "<", "value": 30},
            "sl": 1.0,
            "tp": 2.0,
        }
    )
    assert "RELIANCE" in text
    assert "SL 1.0%" in text
    assert "TP 2.0%" in text
