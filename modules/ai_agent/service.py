from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Callable

from modules.ai_agent.cache import TtlCache
from modules.ai_agent.dsl import DslError, heuristic_parse, plan_text, to_builder_spec, validate_dsl
from modules.ai_agent.rules.suggestor import suggest as rule_suggest
from modules.ai_agent.store import AgentBacktestStore
from modules.backtest_engine import EventDrivenEngine
from modules.shared.contracts import CostModel, DataBundle, Strategy, StrategyConfig, SymbolInfo
from modules.strategy_builder import StrategyBuilder

EXCHANGE_BY_MARKET = {"IN": "NSE", "US": "US", "CRYPTO": "BINANCE"}
CURRENCY_BY_MARKET = {"IN": "INR", "US": "USD", "CRYPTO": "USDT"}
DEFAULT_RANGE_DAYS = {"IN": 365, "US": 365, "CRYPTO": 180}
REVIEW_TTL_SECONDS = 24 * 60 * 60


def _most_common_loss_hour(trades: list) -> int | None:
    hours: dict[int, int] = {}
    for trade in trades:
        if trade.pnl >= 0 or trade.timestamp is None:
            continue
        hour = trade.timestamp.hour
        hours[hour] = hours.get(hour, 0) + 1
    if not hours:
        return None
    return max(hours, key=hours.get)


def build_summary(symbol: str, interval: str, metrics, trades: list) -> str:
    pf = getattr(metrics, "profit_factor", None)
    parts = [f"{metrics.total_trades} trades", f"Win {round(metrics.win_rate_pct)}%"]
    parts.append(f"Max DD {abs(round(metrics.max_drawdown_pct, 1))}%")
    if pf is not None and pf != float("inf"):
        parts.append(f"PF {round(pf, 2)}")
    parts.append(f"Return {round(metrics.total_return_pct, 2)}%")
    hour = _most_common_loss_hour(trades)
    if hour is not None:
        suffix = "pm" if hour >= 12 else "am"
        parts.append(f"Loss hour {hour % 12 or 12}{suffix}")
    return f"{symbol} {interval} — " + ", ".join(parts)


class AgentService:
    def __init__(
        self,
        store: AgentBacktestStore,
        *,
        parser: Callable[[str], dict] | None = None,
        reviewer: Callable[[str], str] | None = None,
        cache: TtlCache | None = None,
    ):
        self._store = store
        self._parser = parser
        self._reviewer = reviewer
        self._cache = cache or TtlCache(REVIEW_TTL_SECONDS)
        self._builder = StrategyBuilder()
        self._engine = EventDrivenEngine()

    def parse(self, text: str) -> dict:
        """Layer 1 listener. Cloudflare parser first, local heuristic fallback."""
        if self._parser is not None:
            try:
                dsl = self._parser(text)
                validate_dsl(dsl)
                return dsl
            except Exception:
                pass
        return heuristic_parse(text)

    def run(self, user_id: str, dsl: dict, fetch_ohlcv: Callable) -> dict:
        """Layer 1 -> run: translate DSL to strategy, backtest, persist."""
        validate_dsl(dsl)
        intent = dsl.get("intent")
        if intent == "review":
            raise DslError("review ke liye /api/agent/review use karo (backtest_id ke saath)")
        symbol = dsl["symbol"].upper()
        market = str(dsl.get("market") or "IN").upper()
        if market not in DEFAULT_RANGE_DAYS:
            raise DslError("market must be IN | US | CRYPTO")

        spec = to_builder_spec(dsl)
        code = self._builder.generate(spec)

        interval = str(dsl.get("interval") or "1d")
        end = date.today()
        start = end - timedelta(days=DEFAULT_RANGE_DAYS[market])
        df = fetch_ohlcv(symbol, interval, start, end)
        if df is None or len(df) == 0:
            raise DslError(f"no data for {symbol} ({interval})")

        symbol_info = SymbolInfo(
            symbol=symbol,
            market=market,
            exchange=EXCHANGE_BY_MARKET[market],
            name=symbol,
            currency=CURRENCY_BY_MARKET[market],
            instrument_type="stock" if market != "CRYPTO" else "crypto",
        )
        bundle = DataBundle(
            symbol=symbol_info, interval=interval, df=df, source="api", data_version="v1"
        )
        strategy = Strategy(
            id="agent",
            version="v1",
            author_user_id="agent",
            code=code,
            config=StrategyConfig(
                stop_loss_pct=float(dsl["sl"]) if dsl.get("sl") is not None else None,
                take_profit_pct=float(dsl["tp"]) if dsl.get("tp") is not None else None,
            ),
        )
        result = self._engine.run(strategy, bundle, CostModel())
        metrics = self._metrics_dict(result)
        summary = build_summary(symbol, interval, result.metrics, result.trades)
        record = self._store.save(
            user_id=user_id,
            dsl=dsl,
            plan_text=plan_text(dsl),
            metrics=metrics,
            summary=summary,
        )
        return {
            "backtest_id": record["id"],
            "metrics": metrics,
            "plan_text": record["plan_text"],
            "summary": summary,
            "code": code,
        }

    def review(self, user_id: str, backtest_id: str) -> dict:
        """Layer 3 brain. Summary-only + 24h cache; Groq/Gemini only on miss."""
        record = self._store.get(user_id, backtest_id)
        if record is None:
            raise DslError("backtest not found")
        summary = record.get("summary") or record.get("plan_text", "")
        metrics = record.get("metrics") or {}
        chips = rule_suggest(metrics)

        key = "agent:review:" + hashlib.sha256(summary.encode()).hexdigest()
        cached = self._cache.get(key)
        if cached:
            return {"review": cached, "chips": chips, "cached": True}

        review = ""
        if self._reviewer is not None:
            try:
                review = (self._reviewer(summary) or "").strip()
            except Exception:
                review = ""
        if not review:
            review = self._fallback_review(summary, chips)
        self._cache.set(key, review)
        return {"review": review, "chips": chips, "cached": False}

    def suggest(self, metrics: dict) -> list[str]:
        """Layer 2 — deterministic chips, no LLM, no limits."""
        return rule_suggest(metrics)

    def history(self, user_id: str, limit: int = 5) -> list[dict]:
        """Recent agent backtests (for review intent: pick latest by symbol)."""
        return [
            {
                "id": r["id"],
                "plan_text": r.get("plan_text", ""),
                "summary": r.get("summary", ""),
                "symbol": str((r.get("dsl") or {}).get("symbol", "")),
                "created_at": r.get("created_at", ""),
            }
            for r in self._store.list(user_id)[:max(1, min(limit, 20))]
        ]

    @staticmethod
    def _fallback_review(summary: str, chips: list[str]) -> str:
        lines = [f"Summary: {summary}"]
        if chips:
            lines.append("Suggestions:")
            lines.extend(f"- {chip}" for chip in chips)
        else:
            lines.append("Backtest solid lag raha hai — isi setup par zyada trades ke liye longer period test karo.")
        return "\n".join(lines)

    @staticmethod
    def _metrics_dict(result) -> dict:
        m = result.metrics
        pf = m.profit_factor if m.profit_factor == m.profit_factor and m.profit_factor != float("inf") else None
        metrics = {
            "total_return_pct": round(m.total_return_pct, 4),
            "cagr_pct": round(m.cagr_pct, 4),
            "sharpe": round(m.sharpe, 4),
            "sortino": round(m.sortino, 4),
            "max_drawdown_pct": round(m.max_drawdown_pct, 4),
            "win_rate_pct": round(m.win_rate_pct, 4),
            "profit_factor": round(pf, 4) if pf is not None else None,
            "total_trades": m.total_trades,
            "avg_trade_return_pct": round(m.avg_trade_return_pct, 4),
            "avg_trade_duration_days": round(m.avg_trade_duration_days, 4),
            "calmar": round(m.calmar, 4),
        }
        hour = _most_common_loss_hour(result.trades)
        if hour is not None:
            metrics["loss_hour"] = hour
        return metrics
