# module: ai-assistant  ★ ISOLATED PROCESS

**Purpose:** The 3-in-1 agent: **Teacher** (explains RSI, volume, candles...), **Listener** (understands typed/spoken strategy in any language), **Doer** (sets up strategy, backtests, paper-trades). Paper-only, every action confirmed.

**Contract:** `AIAssistant` (see `../shared/contracts/README.md`).

## Isolation (owner's #1 rule — this module is the special case)
- Runs as a **separate process/service**. A crash, upgrade, or full AI change NEVER affects other modules.
- Only talks to the app via the `AIAssistant` contract (its tool calls are sandboxed: run_backtest, start_paper_trade, etc.).
- **Provider adapter:** Gemini Flash (free tier) ↔ Ollama (self-host) ↔ paid — swap via config, zero app impact.

## Safety
1. **No real orders. Ever.**
2. Confirm before any strategy save/backtest/paper-trade action.
3. Risk disclaimers on results. No advice framing.
4. Token budgeting to control free-tier cost.

## Full spec
See `docs/product/AI-ASSISTANT.md`.

**Status:** Planning.
