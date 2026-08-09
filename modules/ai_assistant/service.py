from __future__ import annotations

import numpy as np
import pandas as pd

from modules.shared.contracts import AssistantReply
from modules.strategy_engine.sandbox import run_code

PERSONA = """You are the trading coach in a paper-trading platform called trade-forge.
You teach concepts (RSI, moving averages, risk, etc.), listen to the trader's strategy in
any language, and help them turn it into a backtestable strategy.

Current product capabilities already implemented:
- Dashboard with candlestick + volume charts, symbol search, market/index filters, backtesting,
  equity curve, trade table, realistic costs, and CSV export.
- No-code Strategy Builder plus a Python strategy editor.
- Screener with RSI, Bollinger %B, volume ratio, SMA, MACD, sorting, and saved scans.
- Paper Trading with positions, P&L, reset, and backtest-to-paper replay.
- Alerts, Watchlists, Trading Journal, AI journal review, Learn lessons, Hindi/English UI,
  onboarding, mobile responsive layout, command palette, and a floating AI assistant.
- Supported markets: India/NSE (NIFTY 50, NIFTY Bank, NIFTY Total Market, NSE universe),
  US markets and Crypto.

Rules you MUST follow:
- This is a PAPER-TRADING and EDUCATIONAL tool. You never give buy/sell recommendations.
- You never claim guaranteed profits. Always mention risk.
- Do not present an existing capability above as a new feature idea. If asked how to improve
  trade-forge, first acknowledge what already exists, then suggest only genuine gaps or polish.
- Give a concise, prioritized answer with at most 5 actions. Name the relevant tab or workflow.
- If the user asks for an improvement plan, make it specific to trade-forge instead of giving
  generic trading-app advice. Do not end with a vague "what would you like to explore next?".
- If the user describes a trading rule, you may produce strategy code as a single Python
  block. The code must set a variable `signals` (a pandas Series with values in {-1, 0, 1}
  where 1 = long, 0 = flat), computed from `data` (a DataFrame with columns
  open/high/low/close/volume) and optional `params`. You may use pandas as `pd` and numpy
  as `np`. No imports are allowed.
"""


class AIAssistantService:
    def __init__(self, generator, validate_code=None):
        self._generator = generator
        self._pending: dict[str, str] = {}
        self._validate_code = validate_code or self._default_validate

    @staticmethod
    def _default_validate(code: str) -> bool:
        try:
            idx = pd.date_range("2024-01-01", periods=30, freq="B")
            close = pd.Series(range(30), index=idx, dtype=float)
            data = pd.DataFrame(
                {
                    "open": close,
                    "high": close + 1,
                    "low": close - 1,
                    "close": close,
                    "volume": 1000.0,
                },
                index=idx,
            )
            ns = run_code(
                code,
                {"np": np, "pd": pd, "data": data, "params": {}},
                timeout=2.0,
            )
            return isinstance(ns.get("signals"), pd.Series)
        except Exception:
            return False

    def chat(self, user_id: str, message_text_or_audio: str) -> AssistantReply:
        prompt = f"{PERSONA}\n\nTrader's message: {message_text_or_audio}"
        try:
            text = self._generator.generate(prompt)
        except Exception as exc:
            return AssistantReply(
                text=(
                    "AI assistant is temporarily unavailable "
                    f"(provider error: {type(exc).__name__}). "
                    "Try again later."
                )
            )
        action_taken = None
        needs_confirmation = False
        code = self._extract_code(text)
        if code is not None and self._validate_code(code):
            action_taken = "strategy_code_validated"
            self.propose_action(user_id, f"run backtest with generated strategy")
            needs_confirmation = True
        return AssistantReply(
            text=text,
            action_taken=action_taken,
            needs_confirmation=needs_confirmation,
        )

    @staticmethod
    def _extract_code(text: str) -> str | None:
        start = text.find("```")
        end = text.rfind("```")
        if start == -1 or end == start:
            return None
        block = text[start + 3 : end].strip()
        if block.startswith("python"):
            block = block[len("python") :].strip()
        return block

    def propose_action(self, user_id: str, action: str) -> None:
        self._pending[user_id] = action

    def confirm_action(self, user_id: str, proposed_action: str) -> bool:
        if self._pending.get(user_id) == proposed_action:
            self._pending.pop(user_id)
            return True
        return False

    def review_journal(self, user_id: str, entries: list) -> str:
        if not entries:
            return (
                "Koi journal entries nahi mili. Pehle apne trades log karo "
                "(Journal tab se), phir main tumhara review karoonga."
            )
        lines = []
        for e in entries[-30:]:
            tags = ",".join(e.get("tags") or [])
            lines.append(
                "- {sym} {side} pnl={pnl} rating={rating} tags={tags} "
                "note={note} lesson={lesson}".format(
                    sym=e.get("symbol") or "?",
                    side=e.get("side") or "?",
                    pnl=e.get("pnl", 0),
                    rating=e.get("rating"),
                    tags=tags or "-",
                    note=(e.get("note") or "")[:200],
                    lesson=(e.get("lesson") or "")[:100],
                )
            )
        body = "\n".join(lines)
        prompt = (
            f"{PERSONA}\n\n"
            "Ab aap ek trade journal reviewer hain. Trader ne apni journal "
            "entries bheji hain:\n\n"
            f"{body}\n\n"
            "Simple Hinglish mein review do:\n"
            "1) Patterns jo main repeat kar raha hoon (entries se specific evidence do)\n"
            "2) Kya main acha kar raha hoon (strengths)\n"
            "3) Risks / galtiyan jinke liye dhyan rakhna hai\n"
            "4) Agli trade ke liye 2-3 concrete improvements\n\n"
            "Rules: sirf educational, koi buy/sell recommendation nahi, risk ka "
            "zaboor zikr karo, aur entries mein jo nahi hai usse invent mat karo."
        )
        try:
            return self._generator.generate(prompt)
        except Exception as exc:
            return (
                "AI journal review temporarily unavailable "
                f"(provider error: {type(exc).__name__}). Try again later."
            )
