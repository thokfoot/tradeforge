export type Market = "IN" | "US" | "CRYPTO";

export const MARKETS: Market[] = ["IN", "US", "CRYPTO"];
export const MARKET_LABELS: Record<Market, string> = {
  IN: "India / NSE",
  US: "US Markets",
  CRYPTO: "Crypto / 24x7",
};

const BACKEND_URL = "https://tradeforge-api-np0c.onrender.com";
const WAKE_URL = BACKEND_URL.replace(/^http/, "https").replace(/\/api.*$/, "");

export const DEFAULT_BASE_URL = BACKEND_URL;
export const API_URL = BACKEND_URL;

export function wakeBackend(): Promise<boolean> {
  return fetch(`${WAKE_URL}/health`, {
    method: "GET",
    signal: AbortSignal.timeout(70000),
  })
    .then((r) => r.ok)
    .catch(() => false);
}

async function fetchWithRetry<T>(url: string, init?: RequestInit, retries = 2): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 70000);

  try {
    const resp = await fetch(url, { ...init, signal: controller.signal });
    if (!resp.ok) throw new Error(`${resp.status}`);
    return (await resp.json()) as T;
  } catch (e) {
    if (retries > 0) {
      await new Promise((r) => setTimeout(r, 1000));
      return fetchWithRetry<T>(url, init, retries - 1);
    }
    throw e;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetchWithRetry<T>(`${API_URL}${path}`, init);
  return resp;
}

export interface SymbolInfo {
  symbol: string;
  market: string;
  exchange: string;
  name: string;
  currency: string;
  instrument_type: string;
}

export interface Bar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BacktestMetrics {
  total_return_pct: number;
  cagr_pct: number;
  sharpe: number;
  sortino: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  profit_factor: number | null;
  total_trades: number;
  avg_trade_return_pct: number;
  avg_trade_duration_days: number;
  calmar: number;
}

export interface BacktestResult {
  strategy_id: string;
  symbol: string;
  interval: string;
  start: string;
  end: string;
  run_hash: string;
  data_version: string;
  equity_curve: { date: string; equity: number }[];
  trades: {
    order_id: string;
    symbol: string;
    side: string;
    qty: number;
    price: number;
    fees: number;
    pnl: number;
    timestamp: string;
    entry_timestamp: string | null;
  }[];
  metrics: BacktestMetrics;
}

export interface User {
  id: string;
  email: string;
  plan: "free" | "pro";
}

export interface Order {
  id: string;
  user_id: string;
  symbol: string;
  side: string;
  order_type: string;
  qty: number;
  price: number | null;
  stop_price: number | null;
  sl: number | null;
  tp: number | null;
  status: string;
  filled_price: number | null;
  filled_at: string | null;
  created_at: string | null;
}

export interface Position {
  symbol: string;
  qty: number;
  avg_price: number;
  ltp: number;
  unrealized_pnl: number;
  sl: number | null;
  tp: number | null;
}

export interface Account {
  user_id: string;
  balance: number;
  equity: number;
  positions: Position[];
}

export interface Trade {
  order_id: string;
  symbol: string;
  side: string;
  qty: number;
  price: number;
  fees: number;
  pnl: number;
  timestamp: string;
  strategy_id?: string | null;
}

export interface ScreenerRow {
  symbol: string;
  last_close: number;
  change_1d_pct: number | null;
  change_5d_pct: number | null;
  change_1m_pct: number | null;
  change_3m_pct: number | null;
  avg_volume_20: number | null;
  above_sma_50: boolean | null;
  above_sma_200: boolean | null;
  rsi_14: number | null;
  bb_position: number | null;
  vol_ratio_20: number | null;
  above_sma_20: boolean | null;
  macd_above_signal: boolean | null;
}

export interface SavedScan {
  id: string;
  user_id: string;
  name: string;
  market: Market;
  filters: Record<string, unknown>;
  limit: number;
  created_at: string | null;
}

export interface JournalEntry {
  entry_id: string;
  user_id: string;
  trade_id: string;
  note: string;
  symbol: string;
  side: string;
  qty: number;
  pnl: number;
  tags: string[];
  rating: number | null;
  lesson: string;
  created_at: string | null;
}

function json(method: string, body: unknown, token?: string): RequestInit {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  return { method, headers, body: JSON.stringify(body) };
}

export function getSymbols(market: Market): Promise<SymbolInfo[]> {
  return request(`/api/symbols?market=${market}`);
}

export function getOhlcv(
  market: Market,
  symbol: string,
  interval: string = "1d",
  start?: string,
  end?: string
): Promise<{ symbol: string; market: string; interval: string; bars: Bar[] }> {
  // Add .NS suffix for NSE stocks if market is IN and symbol doesn't have it
  let apiSymbol = symbol;
  if (market === "IN" && !symbol.endsWith(".NS") && !symbol.startsWith("NIFTY")) {
    apiSymbol = `${symbol}.NS`;
  }
  const params = new URLSearchParams({ market, interval });
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  const url = `/api/ohlcv/${encodeURIComponent(apiSymbol)}?${params}`;
  console.log("[api] getOhlcv fetching:", url);
  return request(url);
}

export interface BacktestPayload {
  market: Market;
  symbol: string;
  interval: string;
  start: string;
  end: string;
  code: string;
  params: Record<string, number>;
  initial_capital: number;
  position_sizing: "pct" | "fixed";
  position_size: number;
  costs?: Record<string, number>;
}

export function runBacktest(payload: BacktestPayload): Promise<BacktestResult> {
  return request("/api/backtest", json("POST", payload));
}

export function register(email: string, password: string): Promise<{ user: User; token: string }> {
  return request("/api/auth/register", json("POST", { email, password }));
}

export function login(email: string, password: string): Promise<{ user: User; token: string }> {
  return request("/api/auth/login", json("POST", { email, password }));
}

export function subscribe(plan: string, token: string): Promise<User> {
  return request("/api/auth/subscribe", json("POST", { plan }, token));
}

export function saveStrategy(code: string, token: string, id: string = "adhoc"): Promise<{ version: string }> {
  return request("/api/strategies/save", json("POST", { id, code }, token));
}

// ====== AI Agent ======

export interface AgentDsl {
  intent: "create_strategy" | "run_backtest" | "review";
  symbol: string;
  market?: Market;
  interval?: string;
  entry?: { indicator: string; op: string; value: number };
  sl?: number | null;
  tp?: number | null;
}

export interface AgentMetrics {
  total_return_pct: number;
  cagr_pct: number;
  sharpe: number;
  sortino: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  profit_factor: number | null;
  total_trades: number;
  avg_trade_return_pct: number;
  avg_trade_duration_days: number;
  calmar: number;
  loss_hour?: number | null;
}

export interface AgentRecord {
  id: string;
  plan_text: string;
  summary: string;
  symbol: string;
  created_at: string;
}

export function agentParse(text: string, token: string): Promise<{ dsl: AgentDsl; plan_text: string | null }> {
  return request("/api/agent/parse", json("POST", { text }, token));
}

export function agentRun(
  dsl: AgentDsl,
  token: string
): Promise<{ backtest_id: string; metrics: AgentMetrics; plan_text: string; summary: string; code: string }> {
  return request("/api/agent/run", json("POST", { dsl }, token));
}

export function agentReview(
  backtestId: string,
  token: string
): Promise<{ review: string; chips: string[]; cached: boolean }> {
  return request("/api/agent/review", json("POST", { backtest_id: backtestId }, token));
}

export function agentSuggest(metrics: AgentMetrics, token: string): Promise<{ chips: string[] }> {
  return request("/api/agent/suggest", json("POST", { metrics }, token));
}

export function agentHistory(token: string, limit: number = 10): Promise<{ records: AgentRecord[] }> {
  return request(`/api/agent/history?limit=${limit}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export type OrderType = "MARKET" | "LIMIT" | "SL" | "SL-M" | "STOP" | "STOP_LIMIT" | "BRACKET";

export function placeOrder(
  payload: {
    market: Market;
    symbol: string;
    side: "BUY" | "SELL";
    qty: number;
    order_type: OrderType;
    price?: number | null;
    stop_price?: number | null;
    sl?: number | null;
    tp?: number | null;
  },
  token: string
): Promise<Order> {
  return request("/api/paper/order", json("POST", payload, token));
}

export function checkExits(
  market: Market,
  prices: Record<string, number>,
  token: string
): Promise<{ orders: Order[]; count: number }> {
  return request("/api/paper/check-exits", json("POST", { market, prices }, token));
}

export function getAccount(token: string, market: Market): Promise<Account> {
  return request(`/api/paper/account?market=${market}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getPositions(token: string, market: Market): Promise<Position[]> {
  return request(`/api/paper/positions?market=${market}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getHistory(token: string): Promise<Trade[]> {
  return request(`/api/paper/history`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function resetAccount(token: string, market: Market, amount?: number): Promise<Account> {
  const params = new URLSearchParams({ market });
  if (amount != null) params.set("amount", String(amount));
  return request(`/api/paper/reset?${params}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function setLevels(
  token: string,
  market: Market,
  symbol: string,
  sl: number | null,
  tp: number | null
): Promise<Position> {
  return request(
    "/api/paper/position/levels",
    json("POST", { market, symbol, sl, tp }, token)
  );
}

export function replayPaper(
  payload: {
    market: Market;
    symbol: string;
    interval: string;
    start: string;
    end: string;
    code: string;
    params?: Record<string, number>;
    initial_capital?: number;
    position_sizing?: "pct" | "fixed";
    position_size?: number;
    costs?: Record<string, number>;
  },
  token: string
): Promise<{
  symbol: string;
  interval: string;
  fills: number;
  round_trips: number;
  account: Account;
  metrics: { total_return_pct: number; total_trades: number; win_rate_pct: number };
}> {
  return request("/api/paper/replay", json("POST", payload, token));
}

export function startPaperTrading(
  payload: {
    market: Market;
    symbol: string;
    interval: string;
    start: string;
    end: string;
    code: string;
    params?: Record<string, number>;
    initial_capital?: number;
    position_sizing?: "pct" | "fixed";
    position_size?: number;
    costs?: Record<string, number>;
    strategy_id?: string;
  },
  token: string
): Promise<{
  status: string;
  strategy_id: string;
  message: string;
  fills: number;
  round_trips: number;
  account: Account;
  metrics: { total_return_pct: number; total_trades: number; win_rate_pct: number };
}> {
  return request("/api/paper-trading/start", json("POST", payload, token));
}

export function screenerScan(
  market: Market,
  filters: Record<string, unknown>,
  limit: number
): Promise<{ market: Market; scanned: number; count: number; results: ScreenerRow[] }> {
  return request("/api/screener/scan", json("POST", { market, filters, limit }));
}

export function saveScan(
  name: string,
  market: Market,
  filters: Record<string, unknown>,
  limit: number,
  token: string
): Promise<SavedScan> {
  return request("/api/screener/scans/save", json("POST", { name, market, filters, limit }, token));
}

export function listScans(token: string): Promise<SavedScan[]> {
  return request("/api/screener/scans", { headers: { Authorization: `Bearer ${token}` } });
}

export function deleteScan(scanId: string, token: string): Promise<{ deleted: boolean }> {
  return request(`/api/screener/scans/${scanId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function runSavedScan(
  scanId: string,
  token: string
): Promise<{ scan_id: string; name: string; market: Market; scanned: number; count: number; results: ScreenerRow[] }> {
  return request(`/api/screener/scans/${scanId}/run`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function addJournalEntry(
  payload: {
    trade_id: string;
    note: string;
    symbol?: string;
    side?: string;
    qty?: number;
    pnl?: number;
    tags?: string[];
    rating?: number | null;
    lesson?: string;
  },
  token: string
): Promise<JournalEntry> {
  return request("/api/journal/entry", json("POST", payload, token));
}

export function listJournal(token: string): Promise<JournalEntry[]> {
  return request(`/api/journal`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function journalReview(token: string): Promise<{ text: string; entries: number }> {
  return request("/api/journal/review", json("POST", {}, token));
}

export function deleteJournal(entryId: string, token: string): Promise<{ deleted: boolean }> {
  return request(`/api/journal/${entryId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function csvExportUrl(market: Market, symbol: string, interval: string = "1d"): string {
  return `${API_URL}/api/export/csv?market=${market}&symbol=${encodeURIComponent(symbol)}&interval=${interval}`;
}

export interface AlertRule {
  rule_id: string;
  user_id: string;
  symbol: string;
  market: Market;
  metric: "PRICE" | "RSI";
  condition: "ABOVE" | "BELOW";
  value: number;
  active: boolean;
  created_at: string | null;
}

export interface AlertNotification {
  id: string;
  user_id: string;
  rule_id: string;
  symbol: string;
  message: string;
  created_at: string | null;
}

export function listAlerts(token: string): Promise<AlertRule[]> {
  return request("/api/alerts", { headers: { Authorization: `Bearer ${token}` } });
}

export function createAlert(
  token: string,
  body: { symbol: string; market: Market; metric: "PRICE" | "RSI"; condition: "ABOVE" | "BELOW"; value: number }
): Promise<AlertRule> {
  return request("/api/alerts", json("POST", body, token));
}

export function deleteAlert(token: string, ruleId: string): Promise<{ deleted: boolean }> {
  return request(`/api/alerts/${ruleId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function listAlertNotifications(token: string): Promise<AlertNotification[]> {
  return request("/api/alerts/notifications", { headers: { Authorization: `Bearer ${token}` } });
}

export function clearAlertNotifications(token: string): Promise<{ cleared: number }> {
  return request("/api/alerts/notifications/clear", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function checkAlerts(
  token: string
): Promise<{ triggered: number; notifications: AlertNotification[] }> {
  return request("/api/alerts/check", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export interface BuilderCondition {
  indicator: string;
  period?: number | null;
  op: "above" | "below";
  ref?: string | null;
  ref_period?: number | null;
  value?: number | null;
}

export interface BuilderRule {
  op: "AND" | "OR";
  conditions: BuilderCondition[];
}

export function builderGenerate(
  token: string,
  body: { name: string; entry: BuilderRule; exit: BuilderRule }
): Promise<{ name: string; code: string; valid: boolean; errors: string[]; warnings: string[] }> {
  return request("/api/builder/generate", json("POST", body, token));
}
