# shared/contracts — the stable base (sockets)

## Purpose
Single place where ALL module interfaces are defined. Modules never know each other's internals — they only know these contracts. This is how we guarantee "changing one module never breaks another."

## Rule
- Contracts change ONLY via versioning (v1, v2...). Old version keeps working for one release while consumers migrate.
- No module may reach past a contract into another module's code or database.

## Contracts (Phase 1 — define, get owner approval, then implement)

### MarketDataProvider
```python
class MarketDataProvider(Protocol):
    def get_symbols(self) -> list[SymbolInfo]: ...
    def fetch_ohlcv(self, symbol, interval, start, end) -> pd.DataFrame: ...
    def fetch_quote(self, symbol) -> Quote: ...
```
Adapters: NSE, Stooq, Binance, (future: FMP, TwelveData, licensed NSE vendor).

### Strategy
```python
@dataclass
class Strategy:
    id: str
    version: str
    author_user_id: str
    code: str                 # or no-code config (JSON)
    params: dict
    config: StrategyConfig    # entry/exit/risk/costs
    data_version: str

class StrategyService(Protocol):
    def validate(self, s: Strategy) -> ValidationResult: ...
    def save(self, s: Strategy) -> Strategy: ...
    def list_versions(self, strategy_id) -> list[str]: ...
```

### BacktestEngine
```python
class BacktestEngine(Protocol):
    def run(self, strategy: Strategy, data: DataBundle, costs: CostModel) -> BacktestResult: ...
    def metrics(self, result) -> Metrics: ...
    def reproducible_hash(self, strategy, data_version, params) -> str: ...
```

### PaperTrader
```python
class PaperTrader(Protocol):
    def place_order(self, user, symbol, side, qty, order_type, price=None, sl=None, tp=None) -> Order: ...
    def positions(self, user) -> list[Position]: ...
    def history(self, user) -> list[Trade]: ...
    def reset_account(self, user) -> Account: ...
    def parity_score(self, user, strategy_id) -> float: ...
```

### Analytics
```python
class Analytics(Protocol):
    def metrics(self, trades) -> Metrics: ...
    def equity_curve(self, trades) -> Series: ...
    def journal_entry(self, user, trade_id, note) -> None: ...
```

### AIAssistant
```python
class AIAssistant(Protocol):
    def chat(self, user_id, message_text_or_audio) -> AssistantReply: ...   # teacher/listener/doer
    def confirm_action(self, user_id, proposed_action) -> bool: ...
```
Tools it may call (sandboxed): list_markets, lookup_symbol, get_price, get_indicator_value, validate_strategy, run_backtest, start_paper_trade, get_user_learning_state, explain_topic.

### Auth
```python
class AuthService(Protocol):
    def register(self, email, password) -> User: ...
    def login(self, email, password) -> Session: ...
    def create_subscription(self, user, plan) -> ...: ...
```

### Notification
```python
class NotificationService(Protocol):
    def send(self, user, channel, message) -> None: ...
```

## Status
Interfaces above are PROPOSED (Phase 1). Confirm naming/signatures before implementing modules.

## Model changes (implemented, additive only)
- `ScreenerRow` (Screener 2.0, 2026-08-07): added `rsi_14`, `bb_position` (Bollinger %B 0..1), `vol_ratio_20` (last vol / prior-20 avg), `above_sma_20`, `macd_above_signal`. All default `None` — backward compatible with Phase 1 consumers.
