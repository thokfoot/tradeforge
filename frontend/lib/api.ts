export type Market = "IN" | "US" | "CRYPTO";

export const MARKETS: Market[] = ["IN", "US", "CRYPTO"];

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_URL}${path}`, init);
  if (!resp.ok) {
    let detail = "";
    try {
      const body = await resp.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      detail = await resp.text();
    }
    throw new Error(`${resp.status}: ${detail}`);
  }
  return resp.json() as Promise<T>;
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
  const params = new URLSearchParams({ market, interval });
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  return request(`/api/ohlcv/${encodeURIComponent(symbol)}?${params}`);
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

export function assistantChat(message: string, token: string): Promise<{
  text: string;
  action_taken: string | null;
  needs_confirmation: boolean;
}> {
  return request("/api/assistant/chat", json("POST", { user_id: "demo", message }, token));
}

export function assistantConfirm(action: string): Promise<{ confirmed: boolean }> {
  return request("/api/assistant/confirm", json("POST", { user_id: "demo", action }));
}

export function placeOrder(
  payload: {
    user_id: string;
    market: Market;
    symbol: string;
    side: "BUY" | "SELL";
    qty: number;
    order_type: "MARKET" | "LIMIT";
    price?: number | null;
  }
): Promise<Order> {
  return request("/api/paper/order", json("POST", payload));
}

export function getAccount(userId: string, market: Market): Promise<Account> {
  return request(`/api/paper/account?user_id=${userId}&market=${market}`);
}

export function getPositions(userId: string, market: Market): Promise<Position[]> {
  return request(`/api/paper/positions?user_id=${userId}&market=${market}`);
}

export function getHistory(userId: string): Promise<Trade[]> {
  return request(`/api/paper/history?user_id=${userId}`);
}

export function resetAccount(userId: string, market: Market): Promise<Account> {
  return request(`/api/paper/reset?user_id=${userId}&market=${market}`, { method: "POST" });
}

export function screenerScan(
  market: Market,
  filters: Record<string, unknown>,
  limit: number
): Promise<{ market: Market; scanned: number; count: number; results: ScreenerRow[] }> {
  return request("/api/screener/scan", json("POST", { market, filters, limit }));
}

export function addJournalEntry(payload: {
  user_id: string;
  trade_id: string;
  note: string;
  symbol?: string;
  side?: string;
  qty?: number;
  pnl?: number;
  tags?: string[];
  rating?: number | null;
  lesson?: string;
}): Promise<JournalEntry> {
  return request("/api/journal/entry", json("POST", payload));
}

export function listJournal(userId: string): Promise<JournalEntry[]> {
  return request(`/api/journal?user_id=${userId}`);
}

export function deleteJournal(entryId: string, userId: string): Promise<{ deleted: boolean }> {
  return request(`/api/journal/${entryId}?user_id=${userId}`, { method: "DELETE" });
}

export function csvExportUrl(market: Market, symbol: string, interval: string = "1d"): string {
  return `${API_URL}/api/export/csv?market=${market}&symbol=${encodeURIComponent(symbol)}&interval=${interval}`;
}
