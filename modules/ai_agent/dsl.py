from __future__ import annotations

import re

INDICATOR_PERIODS = {
    "RSI": {"indicator": "rsi", "period": 14},
    "MA": {"indicator": "sma", "period": 20},
    "EMA": {"indicator": "ema", "period": 20},
    "SUPERTREND": {"indicator": "sma", "period": 50},
    "CLOSE": {"indicator": "close"},
}

OP_MAP = {"<": "below", ">": "above", "below": "below", "above": "above"}

_SYMBOL_HINT = re.compile(
    r"\b(RELIANCE|TCS|HDFCBANK|INFY|NIFTYBEES|NIFTY|BANKNIFTY|AAPL|TSLA|MSFT|AMZN|GOOGL|META|NVDA|BTCUSDT|ETHUSDT|BNBUSDT)\b",
    re.IGNORECASE,
)
_UPPER_WORD = re.compile(r"\b[A-Z]{2,6}\b")
_NUMBER = re.compile(r"(\d+(?:\.\d+)?)")


class DslError(ValueError):
    pass


def validate_dsl(dsl: dict) -> None:
    if not isinstance(dsl, dict):
        raise DslError("DSL JSON object expected")
    intent = dsl.get("intent")
    if intent not in ("create_strategy", "run_backtest", "review"):
        raise DslError("intent must be create_strategy | run_backtest | review")
    symbol = dsl.get("symbol")
    if not isinstance(symbol, str) or not re.match(r"^[A-Za-z0-9._-]{1,20}$", symbol):
        raise DslError("symbol must be a ticker like RELIANCE or AAPL")
    if intent == "review":
        return
    entry = dsl.get("entry") or {}
    indicator = str(entry.get("indicator") or "RSI").upper()
    if indicator not in INDICATOR_PERIODS:
        raise DslError(f"entry.indicator must be one of {sorted(INDICATOR_PERIODS)}")
    op = str(entry.get("op") or "<").lower()
    if op not in OP_MAP:
        raise DslError("entry.op must be <, >, above or below")
    if entry.get("value") is None:
        raise DslError("entry.value (number) is required")
    try:
        float(entry["value"])
    except (TypeError, ValueError):
        raise DslError("entry.value must be a number")
    for key in ("sl", "tp"):
        if dsl.get(key) is not None:
            try:
                float(dsl[key])
            except (TypeError, ValueError):
                raise DslError(f"{key} must be a number (percent)")


def to_builder_spec(dsl: dict) -> dict:
    """Translate agent DSL into StrategyBuilder spec (see modules/strategy_builder)."""
    validate_dsl(dsl)
    entry = dsl["entry"]
    indicator = str(entry.get("indicator") or "RSI").upper()
    ind = INDICATOR_PERIODS[indicator]
    condition: dict = {
        "indicator": ind["indicator"],
        "op": OP_MAP[str(entry.get("op") or "<").lower()],
        "value": float(entry["value"]),
    }
    if "period" in ind:
        condition["period"] = ind["period"]
    return {
        "entry": {"op": "AND", "conditions": [condition]},
        "exit": {"op": "AND", "conditions": []},
    }


def plan_text(dsl: dict) -> str:
    validate_dsl(dsl)
    symbol = dsl["symbol"].upper()
    if dsl.get("intent") == "review":
        return f"{symbol} ka backtest review karta hoon"
    entry = dsl["entry"]
    ind = str(entry.get("indicator") or "RSI").upper()
    op = str(entry.get("op") or "<").lower()
    value = entry["value"]
    side = "Buy" if op in ("<", "below") else "Sell"
    pieces = [f"{symbol} pe {ind}{op}{value} {side}"]
    if dsl.get("sl"):
        pieces.append(f"SL {dsl['sl']}%")
    if dsl.get("tp"):
        pieces.append(f"TP {dsl['tp']}%")
    return ", ".join(pieces)


def heuristic_parse(text: str) -> dict:
    """Local zero-cost fallback when the Cloudflare parser is unavailable.

    Understands a small Hindi/English subset: "RSI wala bana de",
    "Nifty me RSI 30 se neeche aaye toh lele", "AAPL review karo", etc.
    """
    text = text.strip()
    lower = text.lower()
    if "review" in lower or "analy" in lower or "dekh" in lower:
        intent = "review"
    elif any(
        k in lower
        for k in (
            "bana",
            "karo",
            "karein",
            "kar le",
            "lele",
            "le lo",
            "kharid",
            "bech",
            "buy",
            "sell",
            "test",
            "backtest",
            "strategy",
        )
    ):
        intent = "run_backtest"
    else:
        intent = "create_strategy"

    symbol = None
    match = _SYMBOL_HINT.search(text)
    if match:
        symbol = match.group(1).upper()
    if symbol is None:
        for word in _UPPER_WORD.findall(text):
            if word.upper() in _SYMBOL_HINT.pattern and word.upper() not in (
                "RSI",
                "MA",
                "SL",
                "TP",
            ):
                symbol = word.upper()
                break
    if symbol is None:
        symbol = "RELIANCE"

    if "rsi" in lower:
        indicator = "RSI"
    elif "ma" in lower or "moving average" in lower or "sma" in lower:
        indicator = "MA"
    else:
        indicator = "RSI"

    numbers = [float(n) for n in _NUMBER.findall(text)]
    value = numbers[0] if numbers else 30.0

    if "neeche" in lower or "below" in lower or "<" in text or "kam" in lower or "less" in lower:
        op = "<"
    elif "upar" in lower or "above" in lower or ">" in text or "zyada" in lower:
        op = ">"
    else:
        op = "<"

    dsl: dict = {
        "intent": intent,
        "symbol": symbol,
        "entry": {"indicator": indicator, "op": op, "value": value},
    }
    sl = re.search(r"(?:\bsl[:.\s-]*|\bstop\s*loss[:.\s-]*)(\d+(?:\.\d+)?)", lower)
    tp = re.search(r"(?:\btp[:.\s-]*|\btarget[:.\s-]*)(\d+(?:\.\d+)?)", lower)
    if sl:
        dsl["sl"] = float(sl.group(1))
    if tp:
        dsl["tp"] = float(tp.group(1))
    return dsl
