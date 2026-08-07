# module: ai-assistant — ISOLATED PROCESS

**Purpose:** The 3-in-1 agent: **Teacher** (explains RSI, volume, candles...), **Listener** (understands typed/spoken strategy in any language), **Doer** (sets up strategy, backtests, paper-trades). Paper-only, every action confirmed. **Journal Coach** (reads your journal entries and gives Hinglish feedback).

**Contract:** `AIAssistant` (see `../shared/contracts/README.md`) — `chat`, `propose_action`, `confirm_action`, `review_journal`.

## Isolation (owner's #1 rule — this module is the special case)
- Runs as a **separate process/service**. A crash, upgrade, or full AI change NEVER affects other modules.
- Only talks to the app via the `AIAssistant` contract (its tool calls are sandboxed: run_backtest, start_paper_trade, etc.).
- **Provider adapter:** Gemini Flash (free tier) + Ollama (self-host) + paid — swap via config, zero app impact.

## Methods
- `chat(user_id, message)` → `AssistantReply(text, action_taken?, needs_confirmation?)`; extracts ```python blocks and validates via sandbox; provider errors → friendly fallback text.
- `propose_action(user_id, action)` / `confirm_action(user_id, action)` — pending-action gate for strategy save/backtest/paper-trade.
- `review_journal(user_id, entries)` → str — summarizes last 30 entries (symbol/side/pnl/rating/tags/note/lesson) and asks Gemini for patterns/strengths/risks/improvements (educational only). Wired to `POST /api/journal/review` (Pro).

## Safety
1. **No real orders. Ever.**
2. Confirm before any strategy save/backtest/paper-trade action.
3. Risk disclaimers on results. No advice framing.
4. Token budgeting to control free-tier cost.

## Full spec
See `docs/product/AI-ASSISTANT.md`.

**Status:** Live (Gemini Flash API).
