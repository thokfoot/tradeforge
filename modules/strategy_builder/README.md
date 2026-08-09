# module: strategy-builder — no-code strategy generation

**Purpose:** Turn visual blocks into runnable strategy code. The user picks "BUY when" / "SELL when" conditions (indicator + above/below + threshold or vs-another-indicator, joined with AND/OR); the module generates Python that the backtest engine + sandbox can run directly.

**Contract:** none needed — `StrategyBuilder.generate(spec) -> str` is a pure code generator. The app validates the generated code through `strategy_service().validate()` (sandbox) before returning it.

## Isolation (owner's #1 rule)
- Everything lives in this module: `StrategyBuilder` only produces strings — it never executes code, never imports from another module.
- The generated code intentionally uses only top-level names (`data`, `pd`, `params`) so it runs in both the engine namespace AND the restricted sandbox (which forbids `import` and splits globals/locals — so no helper functions, RSI is precomputed as `rsi_{period}`).

## Supported blocks
- Indicators: `close`, `open`, `high`, `low`, `volume`, `sma(period)`, `ema(period)`, `rsi(period)`.
- Ops: `above` (>), `below` (<).
- Each condition compares an indicator against a number, or against another indicator (e.g. `close above sma20`).
- Entry/exit rules each join their conditions with `AND` or `OR`. Empty exit defaults to `exit = ~entry` (sell when the buy condition turns false).
- State machine: flat → buy on entry bar (fill next open), holding → sell on exit bar (fill next open), matching the engine's 0/1 signal semantics.

## API + frontend
- `app/api/builder.py` — `POST /api/builder/generate` (Pro-gated): spec → `{name, code, valid, errors, warnings}` after a sandbox validation pass.
- Frontend `Strategy Builder` tab: block rows (indicator / period / op / threshold-or-ref / period), AND/OR joins, generated code preview, and an inline backtest runner.

**Status:** Live. 13 tests (9 module + 4 API). Live verified: RSI-pullback spec → valid code → real AAPL daily backtest ran (10 trades, +4.46%).
