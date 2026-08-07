# AI Assistant — Spec (Teacher + Listener + Doer)

> Owner's ask: a non-technical user can type or SPEAK in any language; the AI teaches basics, understands the user, replies in simple words, AND takes action (set strategy → backtest → paper trade).
> "Typing in words, agent doing the rest."

## The 3-in-1 agent

```
User: "RSI kya hota hai?"
  → TEACHER mode: explains in simple Hindi/Hinglish/English with an example.
User: "Toh jab RSI 30 se neeche ho, buy karna, 2% stop loss"
  → LISTENER mode: understands → reflects back in plain words →
     "RSI < 30 → BUY, SL = 2% — sahi hai?"
User: "Haan"
  → DOER mode: creates strategy → runs backtest → shows results → can start paper trade.
```

### Mode rules
- **Teacher:** any concept — RSI, volume, candlesticks, EMA, SL/TP, leverage, P/E, etc. Explain simply, with an example. Educational content generated on demand + curated lessons later.
- **Listener:** convert natural language → **structured strategy JSON** (indicators, conditions, entry/exit, risk). Always confirm in plain words before saving. Handle ambiguity by asking 1–2 clarifying questions ("kitna capital? kab exit? position size?").
- **Doer:** uses app tools through the AIAssistant contract: create strategy, validate, run backtest, start paper trade. **PAPER ONLY — never a real order.** Every consequential action is confirmed by the user first.

## Conversation experience
- Text input + **voice button** (browser speech-to-text — free; Hindi supported).
- Any language (Gemini is strong in Hindi/Hinglish + many others).
- Per-user conversation memory: remembers previous questions/sessions, builds on them ("tumne pichhli baar RSI seekha tha — ab isse strategy banate hain").
- Teaching is progressive: track what the user has learned; suggest next concept.

## Safety (non-negotiable)
1. No real orders. Ever. (Paper mode only.)
2. Confirmation step before saving/executing any strategy.
3. Risk disclaimers on every result screen.
4. No investment advice framing — educational/tool language.
5. Rate-limited to control free-tier AI cost.

## Architecture
- Runs as an **isolated process** (owner's #1 isolation rule) — a change or crash in AI never affects other modules.
- Communicates via `AIAssistant` contract only (inputs: messages, tools it may call; outputs: replies, actions).
- **Provider adapter:** Gemini Flash (free tier) → can swap to Ollama (self-host) or paid models without touching the app.
- Tool calls (sandboxed): `list_markets`, `lookup_symbol`, `get_price`, `get_indicator_value`, `validate_strategy`, `run_backtest`, `start_paper_trade`, `get_user_learning_state`, `explain_topic`.

## Cost control
- Gemini Flash free tier first (₹0). Per-message token budgeting, response length caps, caching of common explanations.
- Plan premium AI add-on only after free tier is exceeded.
