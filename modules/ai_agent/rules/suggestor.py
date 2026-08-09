from __future__ import annotations


def suggest(metrics: dict) -> list[str]:
    """Layer 2 — deterministic improvement chips from backtest metrics.

    Pure if-else rules, no LLM, so it has no limits. Returns at most 3 chips.
    """
    win_rate = _num(metrics.get("win_rate_pct"))
    max_dd = _num(metrics.get("max_drawdown_pct"))
    profit_factor = _num(metrics.get("profit_factor"))
    total_trades = int(metrics.get("total_trades") or 0)
    loss_hour = metrics.get("loss_hour")

    rules: list[tuple[float, str]] = []

    if win_rate is not None and win_rate < 35:
        rules.append((2.0, "SL tight hai — SL ko 1% se 1.5% karke win rate badhao?"))
    elif win_rate is not None and win_rate > 65:
        rules.append((2.0, "Win rate acha hai — ab risk badhakar position size 10% -> 15% karein?"))

    if max_dd is not None and abs(max_dd) > 15:
        rules.append((1.0, f"Max drawdown {abs(max_dd):.0f}% zyada hai — position size 10% -> 5% kar du?"))

    if profit_factor is not None and profit_factor < 1.2:
        rules.append((3.0, "Profit factor low hai — target badhao ya SL chhota karo?"))

    if loss_hour is not None:
        rules.append((1.5, f"{loss_hour} baje ke baad losses zyada hain — us time trade avoid karein?"))

    if total_trades < 20 and total_trades > 0:
        rules.append((2.5, "Sirf {total} trades hain — zyada samples ke liye longer period test karein?".format(total=total_trades)))

    rules.sort(key=lambda item: item[0], reverse=True)
    return [text for _, text in rules][:3]


def _num(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
