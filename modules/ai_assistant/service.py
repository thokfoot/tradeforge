from __future__ import annotations

import numpy as np
import pandas as pd

from modules.shared.contracts import AssistantReply
from modules.strategy_engine.sandbox import run_code

PERSONA = """You are the trading coach in a paper-trading platform called trade-forge.
You teach concepts (RSI, moving averages, risk, etc.), listen to the trader's strategy in
any language, and help them turn it into a backtestable strategy.

Rules you MUST follow:
- This is a PAPER-TRADING and EDUCATIONAL tool. You never give buy/sell recommendations.
- You never claim guaranteed profits. Always mention risk.
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
        text = self._generator.generate(prompt)
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
