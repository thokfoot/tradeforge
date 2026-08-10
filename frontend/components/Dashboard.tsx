"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createChart, LineSeries, type Time } from "lightweight-charts";
import { ChevronDown, Eye, Gauge, HelpCircle, Layers, Receipt, Settings2, Wallet } from "lucide-react";
import Chart from "@/components/Chart";
import {
  csvExportUrl,
  getOhlcv,
  getSymbols,
  replayPaper,
  runBacktest,
  saveStrategy,
  startPaperTrading,
  MARKETS,
  MARKET_LABELS,
  type BacktestResult,
  type Bar,
  type Market,
  type SymbolInfo,
  type User,
} from "@/lib/api";

const INTERVALS = [
  { value: "1d", label: "1D" },
  { value: "1h", label: "1H" },
  { value: "1m", label: "1M" },
];

const INTERVALS_BY_MARKET: Record<Market, string[]> = {
  IN: ["1d"],
  US: ["1d", "1h", "1m"],
  CRYPTO: ["1d", "1h", "1m"],
};

const DEFAULT_SYMBOLS: Record<Market, string> = {
  IN: "RELIANCE.NS",
  US: "AAPL",
  CRYPTO: "BTCUSDT",
};

const PAGE_SIZE = 10;

type PositionSizing = "pct" | "fixed";

function defaultReality(market: Market) {
  return {
    initialCapital: 100000,
    positionSizing: "pct" as PositionSizing,
    positionSize: 10,
    brokerage: market === "IN" ? 20 : 0,
    slippagePct: market === "CRYPTO" ? 0.1 : 0.05,
  };
}

function costsFor(market: Market, brokerage: number, slippagePct: number): Record<string, number> {
  if (market === "IN") {
    return {
      brokerage,
      stt_pct: 0.001,
      exchange_charges_pct: 0.0000345,
      sebi_fees_pct: 0.000001,
      gst_pct: 0.18,
      stamp_duty_pct: 0.00015,
      slippage_pct: slippagePct / 100,
    };
  }
  return {
    brokerage_pct: market === "CRYPTO" ? 0.001 : 0,
    slippage_pct: slippagePct / 100,
  };
}

function startDateFor(interval: string): string {
  const days = interval === "1m" ? 7 : interval === "1h" ? 60 : 2191;
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

function chartStartDateFor(interval: string): string {
  const days = interval === "1m" ? 7 : interval === "1h" ? 45 : 180;
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

const DEFAULT_CODE = `# signals: 1 = buy, 0 = no action, -1 = sell
# available: data (open/high/low/close/volume), params, pd, np
fast = params.get("fast", 10)
slow = params.get("slow", 30)
ma_fast = data["close"].rolling(fast, min_periods=1).mean()
ma_slow = data["close"].rolling(slow, min_periods=1).mean()

# Crossover: 1 on cross-up, -1 on cross-down, 0 otherwise
prev_fast_above = ma_fast.shift(1) > ma_slow.shift(1)
curr_fast_above = ma_fast > ma_slow
signals = pd.Series(0, index=data.index)
signals[curr_fast_above & ~prev_fast_above] = 1
signals[~curr_fast_above & prev_fast_above] = -1
signals = signals.fillna(0)`;

const STRATEGY_TEMPLATES = [
  {
    id: "sma",
    label: "SMA crossover",
    description: "Trend following",
    code: DEFAULT_CODE,
  },
  {
    id: "rsi",
    label: "RSI reversal",
    description: "Mean reversion",
    code: `# Buy below RSI threshold, exit/short above it (params-driven)
period = params.get("period", 14)
buy_below = params.get("buy_below", 30)
sell_above = params.get("sell_above", 70)
delta = data["close"].diff()
gain = delta.clip(lower=0).rolling(period).mean()
loss = (-delta.clip(upper=0)).rolling(period).mean()
relative_strength = gain / loss.replace(0, np.nan)
rsi = 100 - (100 / (1 + relative_strength))
signals = ((rsi < buy_below).astype(int) - (rsi > sell_above).astype(int)).fillna(0)`,
  },
  {
    id: "breakout",
    label: "20-bar breakout",
    description: "Momentum",
    code: `# Enter on a close above the prior 20-bar high
lookback = params.get("lookback", 20)
prior_high = data["high"].rolling(lookback).max().shift(1)
prior_low = data["low"].rolling(lookback).min().shift(1)
signals = ((data["close"] > prior_high).astype(int) - (data["close"] < prior_low).astype(int)).fillna(0)`,
  },
];

const TEMPLATE_PARAMS: Record<string, { key: string; label: string; defaultValue: number }[]> = {
  sma: [
    { key: "fast", label: "Fast MA", defaultValue: 10 },
    { key: "slow", label: "Slow MA", defaultValue: 30 },
  ],
  rsi: [
    { key: "period", label: "RSI period", defaultValue: 14 },
    { key: "buy_below", label: "Buy below", defaultValue: 30 },
    { key: "sell_above", label: "Sell above", defaultValue: 70 },
  ],
  breakout: [{ key: "lookback", label: "Lookback", defaultValue: 20 }],
};

function defaultParamsFor(id: string): Record<string, number> {
  const fields = TEMPLATE_PARAMS[id] ?? [];
  return Object.fromEntries(fields.map((field) => [field.key, field.defaultValue]));
}

function toIndian(n: number): string {
  const s = Math.round(n).toString();
  if (s.length <= 3) return s;
  const last3 = s.slice(-3);
  const rest = s.slice(0, -3);
  return rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + last3;
}

function formatDuration(days: number): string {
  if (!days || days <= 0) return "—";
  if (days >= 1) return `${days.toFixed(1)}d`;
  const hours = days * 24;
  if (hours >= 1) return `${hours.toFixed(1)}h`;
  return `${Math.max(1, Math.round(days * 24 * 60))}m`;
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "up" | "down" }) {  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className={`metric-value${value === "—" ? " muted" : ""}`} style={tone === "up" ? { color: "var(--up)" } : tone === "down" ? { color: "var(--down)" } : undefined}>
        {value}
      </div>
    </div>
  );
}

function toTime(date: string): Time {
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(date)) {
    return Math.floor(new Date(date.replace(" ", "T")).getTime() / 1000) as Time;
  }
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(date)) {
    return Math.floor(new Date(date).getTime() / 1000) as Time;
  }
  return date as Time;
}

function isFlatCurve(curve: { date: string; equity: number }[]): boolean {
  if (curve.length < 2) return false;
  const first = curve[0].equity;
  return curve.every((p) => p.equity === first);
}

function EquityChart({ curve, height = 300 }: { curve: { date: string; equity: number }[]; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const chart = createChart(el, {
      width: el.clientWidth,
      height,
      layout: { background: { color: "transparent" }, textColor: "#7a89b0", fontSize: 12 },
      grid: {
        vertLines: { color: "rgba(26,37,64,0.45)" },
        horzLines: { color: "rgba(26,37,64,0.45)" },
      },
      rightPriceScale: { borderColor: "#1a2540", scaleMargins: { top: 0.08, bottom: 0.08 } },
      timeScale: { borderColor: "#1a2540" },
      crosshair: { mode: 0 },
    });
    const s = chart.addSeries(LineSeries, {
      color: "#14e8b0",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
    });
    s.setData(curve.map((p) => ({ time: toTime(p.date), value: p.equity })));
    chart.timeScale().fitContent();
    const onResize = () => {
      if (ref.current) chart.applyOptions({ width: ref.current.clientWidth });
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.remove();
    };
  }, [curve, height]);
  return <div ref={ref} className="equity-wrap" style={{ height }} />;
}

export default function Dashboard({ token, user, onNavigate }: {
  token: string | null;
  user: User | null;
  onNavigate?: (tab: "builder" | "learn" | "paper" | "alerts") => void;
}) {
  const [market, setMarket] = useState<Market>("IN");
  const [symbols, setSymbols] = useState<SymbolInfo[]>([]);
  const [marketFilter, setMarketFilter] = useState("ALL");
  const [symbol, setSymbol] = useState("");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [interval, setInterval] = useState("1d");
  const [bars, setBars] = useState<Bar[]>([]);
  const [reloadNonce, setReloadNonce] = useState(0);
  const [loading, setLoading] = useState(false);
  const [ohlcvError, setOhlcvError] = useState("");
  const [code, setCode] = useState(DEFAULT_CODE);
  const [templateId, setTemplateId] = useState("sma");
  const [initialCapital, setInitialCapital] = useState(100000);
  const [positionSizing, setPositionSizing] = useState<PositionSizing>("pct");
  const [positionSize, setPositionSize] = useState(10);
  const [brokerage, setBrokerage] = useState(0);
  const [slippagePct, setSlippagePct] = useState(0.05);
  const [chartType, setChartType] = useState<"candles" | "line">("candles");
  const [showVolume, setShowVolume] = useState(true);
  const [strategyParams, setStrategyParams] = useState<Record<string, number>>(defaultParamsFor("sma"));
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [replayMsg, setReplayMsg] = useState("");
  const [ctaMsg, setCtaMsg] = useState("");
  const [ctaBusy, setCtaBusy] = useState(false);
  const [focusedTrade, setFocusedTrade] = useState<string | null>(null);
  const [showHero, setShowHero] = useState<boolean>(true);
  useEffect(() => {
    try {
      if (localStorage.getItem("tf_hide_hero") === "1" || localStorage.getItem("tf_ran_backtest") === "1") {
        setShowHero(false);
      }
    } catch {
      // ignore storage errors
    }
  }, []);
  const [realityOpen, setRealityOpen] = useState(false);
  const [resultTab, setResultTab] = useState<"equity" | "trades" | "logs">("equity");
  const [tradePage, setTradePage] = useState(0);
  const [chartH, setChartH] = useState(520);
  const gutterRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const sync = () => {
      const w = window.innerWidth;
      setChartH(w <= 640 ? 300 : w <= 960 ? 380 : w < 1280 ? 460 : 520);
    };
    sync();
    window.addEventListener("resize", sync);
    return () => window.removeEventListener("resize", sync);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setInterval("1d");
    const reality = defaultReality(market);
    setInitialCapital(reality.initialCapital);
    setPositionSizing(reality.positionSizing);
    setPositionSize(reality.positionSize);
    setBrokerage(reality.brokerage);
    setSlippagePct(reality.slippagePct);
    setSymbols([]);
    setMarketFilter("ALL");
    setSymbol("");
    setQuery("");
    setBars([]);
    setResult(null);
    getSymbols(market)
      .then((s) => {
        if (cancelled) return;
        setSymbols(s);
        const first = s.find((item) => item.symbol === DEFAULT_SYMBOLS[market])?.symbol ?? s[0]?.symbol ?? DEFAULT_SYMBOLS[market];
        setSymbol(first);
        setQuery(first);
      })
      .catch((e) => setOhlcvError(String(e.message ?? e)));
    return () => {
      cancelled = true;
    };
  }, [market]);

  useEffect(() => {
    if (!symbol) return;
    console.log("Loading symbol:", symbol);
    let cancelled = false;
    setBars([]);
    setOhlcvError("");
    setLoading(true);
    getOhlcv(
      market,
      symbol,
      interval,
      chartStartDateFor(interval),
      new Date().toISOString().slice(0, 10)
    )
      .then((r) => {
        if (cancelled) return;
        setBars(r.bars);
      })
      .catch((e) => setOhlcvError(String(e.message ?? e)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [market, symbol, interval, reloadNonce]);

  const indexSymbols = useMemo(
    () => symbols.filter((item) => item.instrument_type === "index"),
    [symbols]
  );

  const filteredSymbols = useMemo(() => {
    if (marketFilter === "INDICES") return indexSymbols;
    if (marketFilter === "STOCKS") return symbols.filter((item) => item.instrument_type !== "index");
    if (marketFilter !== "ALL") return symbols.filter((item) => item.symbol === marketFilter);
    return symbols;
  }, [indexSymbols, marketFilter, symbols]);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return filteredSymbols.slice(0, 10);
    return filteredSymbols
      .filter((s) => s.symbol.toLowerCase().includes(q) || (s.name ?? "").toLowerCase().includes(q))
      .slice(0, 10);
  }, [filteredSymbols, query]);

  function onMarketFilterChange(value: string) {
    setMarketFilter(value);
    const pool = value === "INDICES"
      ? indexSymbols
      : value === "STOCKS"
        ? symbols.filter((item) => item.instrument_type !== "index")
        : value === "ALL"
          ? symbols
          : symbols.filter((item) => item.symbol === value);
    const next = pool.find((item) => item.symbol === symbol) ?? pool[0];
    if (next) {
      setSymbol(next.symbol);
      setQuery(next.symbol);
    }
  }

  function pick(sym: string) {
    setSymbol(sym);
    setQuery(sym);
    setOpen(false);
  }

  function chooseTemplate(id: string) {
    const template = STRATEGY_TEMPLATES.find((item) => item.id === id);
    if (!template) return;
    setTemplateId(id);
    setCode(template.code);
    setStrategyParams(defaultParamsFor(id));
    setError("");
  }

  useEffect(() => {
    if (result) {
      setShowHero(false);
      try { localStorage.setItem("tf_ran_backtest", "1"); } catch {}
      setTradePage(0);
    }
  }, [result]);

  function dismissHero() {
    setShowHero(false);
    try { localStorage.setItem("tf_hide_hero", "1"); } catch {}
  }

  function showHeroAgain() {
    setShowHero(true);
    try { localStorage.removeItem("tf_hide_hero"); } catch {}
  }

  const quote = useMemo(() => {
    if (bars.length < 2) return null;
    const last = bars[bars.length - 1];
    const prev = bars[bars.length - 2];
    const chg = ((last.close - prev.close) / prev.close) * 100;
    const hi = Math.max(...bars.map((b) => b.high));
    const lo = Math.min(...bars.map((b) => b.low));
    const cur = symbols.find((s) => s.symbol === symbol);
    return { last, chg, hi, lo, name: cur?.name ?? "" };
  }, [bars, symbols, symbol]);

  async function doRun() {
    setRunning(true);
    setError("");
    setResult(null);
    try {
      const res = await runBacktest({
        market,
        symbol,
        interval,
        start: startDateFor(interval),
        end: new Date().toISOString().slice(0, 10),
        code,
        params: strategyParams,
        initial_capital: initialCapital,
        position_sizing: positionSizing,
        position_size: positionSize,
        costs: costsFor(market, brokerage, slippagePct),
      });
      setResult(res);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setRunning(false);
    }
  }

  const onRun = doRun;

  const autoRanRef = useRef<string>("");
  useEffect(() => {
    if (running || !symbol || market !== "IN") return;
    const key = `${market}:${symbol}`;
    if (autoRanRef.current === key) return;
    autoRanRef.current = key;
    void doRun();
  }, [market, symbol, running]);

  async function onReplay() {
    if (!token) return;
    setReplayMsg("Replaying...");
    setError("");
    try {
      const res = await replayPaper({
        market,
        symbol,
        interval,
        start: startDateFor(interval),
        end: new Date().toISOString().slice(0, 10),
        code,
        initial_capital: initialCapital,
        position_sizing: positionSizing,
        position_size: positionSize,
        costs: costsFor(market, brokerage, slippagePct),
      }, token);
      setReplayMsg(
        `Replayed ${res.round_trips} round trips · paper equity ₹${res.account.equity.toFixed(0)} · return ${res.metrics.total_return_pct}%`
      );
    } catch (e) {
      setReplayMsg("");
      setError(String((e as Error).message ?? e));
    }
  }

  async function onSave() {
    setError("");
    try {
      await saveStrategy(code, token!);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  }

  async function onStartPaperTrading() {
    if (!token) {
      setCtaMsg("");
      setError("Login to start paper trading this strategy");
      return;
    }
    setCtaBusy(true);
    setError("");
    try {
      await startPaperTrading({
        market,
        symbol,
        interval,
        start: startDateFor(interval),
        end: new Date().toISOString().slice(0, 10),
        code,
        params: strategyParams,
        initial_capital: initialCapital,
        position_sizing: positionSizing,
        position_size: positionSize,
        costs: costsFor(market, brokerage, slippagePct),
        strategy_id: "adhoc",
      }, token);
      setCtaMsg("Paper trading started - you'll get Telegram updates");
    } catch (e) {
      setCtaMsg("");
      setError(String((e as Error).message ?? e));
    } finally {
      setCtaBusy(false);
    }
  }

  function stepParam(key: string, delta: number) {
    setStrategyParams((prev) => ({ ...prev, [key]: Math.max(1, Math.round((prev[key] ?? 0) + delta)) }));
  }

  const m = result?.metrics;

  const zones = useMemo(() => {
    if (!result) return [];
    return result.trades
      .filter((t) => t.entry_timestamp)
      .map((t) => ({
        entryTime: t.entry_timestamp as string,
        exitTime: t.timestamp,
        entryPrice: t.price - (t.pnl + t.fees) / t.qty,
        exitPrice: t.price,
        pnl: t.pnl,
      }));
  }, [result]);

  const pagedTrades = useMemo(() => {
    if (!result) return [];
    return result.trades.slice(tradePage * PAGE_SIZE, tradePage * PAGE_SIZE + PAGE_SIZE);
  }, [result, tradePage]);

  const closedCount = useMemo(() => (result ? result.trades.filter((t) => t.entry_timestamp).length : 0), [result]);

  const costHint = `Net P&L is after Indian costs: Brokerage ₹${brokerage}/order · STT ${((costsFor(market, brokerage, slippagePct).stt_pct ?? 0) * 100).toFixed(2)}% · GST 18% · Stamp ${((costsFor(market, brokerage, slippagePct).stamp_duty_pct ?? 0) * 100).toFixed(2)}% · Slippage ${slippagePct}% on every fill`;

  return (
    <div className="dash-shell">
      {!showHero && (
        <button className="hero-return" type="button" aria-label="Show intro banner" title="Show intro" onClick={showHeroAgain}>?</button>
      )}
      {showHero && (
      <section className="dashboard-hero">
        <button className="hero-dismiss" type="button" aria-label="Dismiss intro banner" onClick={dismissHero}>×</button>
        <div className="hero-copy">
          <div className="eyebrow"><span className="eyebrow-mark" />PAPER TRADING LAB</div>
          <h2>Turn a market idea into a tested edge.</h2>
          <p>Explore price action, write a rule, and validate the decision before capital is ever at risk.</p>
          <div className="hero-steps">
            <div className="hero-step"><b>01</b><span>Explore</span></div>
            <div className="hero-step"><b>02</b><span>Backtest</span></div>
            <div className="hero-step"><b>03</b><span>Replay</span></div>
          </div>
          <div className="hero-actions">
            <button className="hero-button-primary" type="button" onClick={() => onNavigate?.("builder")}>Build with blocks <span>→</span></button>
            <button className="hero-button-secondary" type="button" onClick={() => onNavigate?.("learn")}>Start with Learn</button>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="hero-grid" />
          <div className="hero-orbit hero-orbit-one" />
          <div className="hero-orbit hero-orbit-two" />
          <div className="hero-core"><span>TF</span><small>EDGE</small></div>
          <span className="hero-node hero-node-one">DATA</span>
          <span className="hero-node hero-node-two">RULES</span>
          <span className="hero-node hero-node-three">RISK</span>
        </div>
      </section>
      )}

      <div className="controls-card">
        <div className="form-group">
          <div className="form-label">Market</div>
          <div className="market-row">
            <button
              type="button"
              className={`segmented-pill ${market === "IN" ? "on" : ""}`}
              onClick={() => setMarket("IN")}
            >
              India / NSE
            </button>
            <select
              className="more-markets"
              aria-label="More markets"
              value={market === "IN" ? "" : market}
              onChange={(event) => { if (event.target.value) setMarket(event.target.value as Market); }}
            >
              <option value="" disabled hidden>More markets</option>
              {MARKETS.filter((mk) => mk !== "IN").map((mk) => (
                <option key={mk} value={mk}>{MARKET_LABELS[mk]}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group market-filter">
          <div className="form-label">Universe / Index</div>
          <select value={marketFilter} onChange={(event) => onMarketFilterChange(event.target.value)}>
            <option value="ALL">All instruments</option>
            {market === "IN" && <option value="STOCKS">All NSE stocks</option>}
            {indexSymbols.length > 0 && <option value="INDICES">All indices</option>}
            {indexSymbols.map((item) => (
              <option key={item.symbol} value={item.symbol}>{item.name} ({item.symbol})</option>
            ))}
          </select>
        </div>

        <div className="form-group symbol-search">
          <div className="form-label">Symbol</div>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setOpen(true)}
            onBlur={() => setTimeout(() => setOpen(false), 120)}
            placeholder="Search symbol…"
          />
          {open && matches.length > 0 && (
            <div className="symbol-dropdown">
              {matches.map((s) => (
                <button key={s.symbol} className="symbol-option" onMouseDown={() => pick(s.symbol)}>
                  <b>{s.symbol}</b>
                  <span>{s.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="spacer" />
        {symbol && (
          <a className="btn-secondary btn-sm csv-link" href={csvExportUrl(market, symbol)}>
            ⬇ CSV
          </a>
        )}
      </div>

      {quote && (
        <div className="price-header">
          <b className="ph-symbol">{symbol}</b>
          {quote.name && quote.name !== symbol && <span className="ph-name">{quote.name}</span>}
          <span className="ph-price">{quote.last.close.toFixed(2)}</span>
          <span className={`ph-change ${quote.chg >= 0 ? "up" : "down"}`}>
            {quote.chg >= 0 ? "▲" : "▼"} {quote.chg.toFixed(2)}%
          </span>
          <span className="ph-sep" />
          <span className="ph-stat"><i>OPEN</i> <b>{quote.last.open.toFixed(2)}</b></span>
          <span className="ph-stat"><i>HIGH</i> <b>{quote.last.high.toFixed(2)}</b></span>
          <span className="ph-stat"><i>LOW</i> <b>{quote.last.low.toFixed(2)}</b></span>
          <span className="ph-stat"><i>52W H/L</i> <b>{quote.hi.toFixed(2)} / {quote.lo.toFixed(2)}</b></span>
          <span className="ph-stat ph-volume"><i>VOLUME</i> <b>{toIndian(quote.last.volume)}</b></span>
        </div>
      )}

      <div className="dashboard-body">
        <div className="dash-main">

          <section className="card chart-card">
            <div className="chart-toolbar">
              <div className="segmented chart-type">
                <button type="button" className={chartType === "candles" ? "on" : ""} onClick={() => setChartType("candles")}>Candles</button>
                <button type="button" className={chartType === "line" ? "on" : ""} onClick={() => setChartType("line")}>Line</button>
              </div>
              <div className="chart-tool-divider" />
              <div className="segmented">
                {INTERVALS.filter((i) => INTERVALS_BY_MARKET[market].includes(i.value)).map((i) => (
                  <button key={i.value} type="button" className={interval === i.value ? "on" : ""} onClick={() => setInterval(i.value)}>
                    {i.label}
                  </button>
                ))}
              </div>
              <div className="chart-tool-divider" />
              <button type="button" className={`chart-tool-btn ${showVolume ? "on" : ""}`} onClick={() => setShowVolume((v) => !v)} title="Toggle volume pane">
                <Eye size={13} /> Volume
              </button>
              <div className="spacer" />
            </div>
            {loading ? (
              <div className="chart-loading" style={{ height: chartH }}>
                <div className="skeleton" style={{ height: chartH, margin: 0, borderRadius: 0 }} />
                <div className="chart-loading-label">Loading live prices…</div>
              </div>
            ) : (
              <Chart bars={bars} type={chartType} showVolume={showVolume} height={chartH} tradeMarkers={result?.trades ?? []} tradeZones={zones} focusTime={focusedTrade} />
            )}
            {ohlcvError && !loading && (
              <div className="data-error-state">
                <div className="data-error-title">Data is temporarily unavailable</div>
                <p>Select another instrument or retry this market connection.</p>
                <button className="btn-secondary btn-sm" type="button" onClick={() => setReloadNonce((value) => value + 1)}>Retry data</button>
                <details>
                  <summary>Technical details</summary>
                  <code>{ohlcvError}</code>
                </details>
              </div>
            )}
          </section>

          <section className="card bt-metrics">
            <div className="metrics-grid-3x2">
              <Metric label="CAGR" value={m ? `${m.cagr_pct.toFixed(2)}%` : "—"} tone={m && m.cagr_pct >= 0 ? "up" : undefined} />
              <Metric label="Sharpe" value={m ? m.sharpe.toFixed(2) : "—"} />
              <Metric label="Max DD" value={m ? `${m.max_drawdown_pct.toFixed(2)}%` : "—"} tone={m ? "down" : undefined} />
              <Metric label="Win %" value={m ? `${m.win_rate_pct.toFixed(1)}%` : "—"} />
              <Metric label="Profit factor" value={m ? (m.profit_factor === null ? "∞" : m.profit_factor.toFixed(2)) : "—"} />
              <Metric label="Avg trade" value={m ? `${m.avg_trade_return_pct.toFixed(2)}%` : "—"} tone={m && m.avg_trade_return_pct >= 0 ? "up" : undefined} />
            </div>
          </section>

          <section className="card bt-results">
            {result && m ? (
              <>
                <div className="result-tabs" role="tablist">
                  <button type="button" role="tab" aria-selected={resultTab === "equity"} className={resultTab === "equity" ? "on" : ""} onClick={() => setResultTab("equity")}>Equity Curve</button>
                  <button type="button" role="tab" aria-selected={resultTab === "trades"} className={resultTab === "trades" ? "on" : ""} onClick={() => setResultTab("trades")}>Trades</button>
                  <button type="button" role="tab" aria-selected={resultTab === "logs"} className={resultTab === "logs" ? "on" : ""} onClick={() => setResultTab("logs")}>Logs</button>
                </div>

                {resultTab === "equity" && (
                  <div>
                    <div className="result-subhead">
                      <span className="card-title">{result.symbol} · {result.interval}</span>
                      <span className="result-meta">{result.start} → {result.end}</span>
                      <span className="result-meta">Avg hold <b>{formatDuration(m.avg_trade_duration_days)}</b></span>
                      <span className="result-meta result-net">Net P&amp;L {m.total_return_pct >= 0 ? "+" : "−"}₹{Math.abs((initialCapital * m.total_return_pct) / 100).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                      <span className="chip"><span className="text-muted">run</span> {result.run_hash.slice(0, 8)}</span>
                      <span className="cost-hint" title={costHint}><HelpCircle size={13} /> Indian costs</span>
                    </div>
                    {result.equity_curve.length > 0 && !isFlatCurve(result.equity_curve) ? (
                      <EquityChart curve={result.equity_curve} height={300} />
                    ) : (
                      <div className="empty-state">
                        <div className="empty-icon">📈</div>
                        <div className="empty-title">Flat equity</div>
                        No price movement over this window
                      </div>
                    )}
                    <div className="cta-bar">
                      <button
                        className="btn-cta-primary"
                        type="button"
                        onClick={onStartPaperTrading}
                        disabled={ctaBusy}
                      >
                        {ctaBusy ? "Starting…" : "▶ Start Paper Trading this Strategy"}
                      </button>
                      <button className="btn-cta-secondary" type="button" onClick={() => onNavigate?.("alerts")}>
                        🔔 Set Alert
                      </button>
                      {ctaMsg && <span className="cta-msg">{ctaMsg}</span>}
                    </div>
                  </div>
                )}

                {resultTab === "trades" && (
                  <div>
                    <div className="table-wrap tabular trades-table">
                      <table>
                        <thead>
                          <tr><th>time</th><th>side</th><th className="num">qty</th><th className="num">price</th><th className="num">pnl</th></tr>
                        </thead>
                        <tbody>
                          {pagedTrades.map((t) => (
                            <tr
                              key={t.order_id}
                              onClick={() => setFocusedTrade(t.timestamp)}
                              className={focusedTrade === t.timestamp ? "trade-row-active" : ""}
                              style={{ cursor: "pointer" }}
                            >
                              <td>{t.timestamp.slice(0, interval.endsWith("d") ? 10 : 16)}</td>
                              <td className={`trade-side ${t.side === "BUY" ? "buy" : "sell"}`}>{t.side}</td>
                              <td className="num">{t.qty}</td>
                              <td className="num">{t.price.toFixed(2)}</td>
                              <td className={`num trade-pnl ${t.pnl >= 0 ? "up" : "down"}`}>{t.pnl.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="pagination">
                      <span className="pag-info">{result.trades.length === 0 ? 0 : tradePage * PAGE_SIZE + 1}–{Math.min((tradePage + 1) * PAGE_SIZE, result.trades.length)} of {result.trades.length}</span>
                      <button className="btn-secondary btn-sm" type="button" disabled={tradePage === 0} onClick={() => setTradePage((p) => Math.max(0, p - 1))}>‹ Prev</button>
                      <button className="btn-secondary btn-sm" type="button" disabled={tradePage >= Math.max(0, Math.ceil(result.trades.length / PAGE_SIZE) - 1)} onClick={() => setTradePage((p) => p + 1)}>Next ›</button>
                    </div>
                  </div>
                )}

                {resultTab === "logs" && (
                  <div className="log-list">
                    <div className="log-row"><span>Run hash</span><code>{result.run_hash}</code></div>
                    <div className="log-row"><span>Window</span><code>{result.start} → {result.end}</code></div>
                    <div className="log-row"><span>Interval</span><code>{result.interval}</code></div>
                    <div className="log-row"><span>Data version</span><code>{result.data_version}</code></div>
                    <div className="log-row"><span>Trade rows</span><code>{result.trades.length}</code></div>
                    <div className="log-row"><span>Closed trades</span><code>{closedCount}</code></div>
                    <div className="log-row"><span>Cost model</span><code>{market === "IN" ? `Brokerage ₹${brokerage}/order · STT 0.1% · GST 18% · Stamp 0.015% · Slippage ${slippagePct}%` : `Slippage ${slippagePct}%`}</code></div>
                  </div>
                )}
              </>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">▶</div>
                <div className="empty-title">No backtest yet</div>
                <div className="empty-text">Write a strategy and hit Run Backtest</div>
                <button className="btn-run" onClick={onRun} disabled={running || !symbol}>Run Backtest</button>
              </div>
            )}
          </section>
        </div>

        <aside className="card bt-editor">
          <div className="card-header">
            <div>
              <div className="card-title">Strategy Editor</div>
              <div className="card-subtitle">Python — signals: 1 = long, 0 = flat, -1 = short</div>
            </div>
          </div>

          <div className="reality-settings">
            <button className="reality-toggle" type="button" onClick={() => setRealityOpen((o) => !o)} aria-expanded={realityOpen}>
              <Settings2 size={14} className="reality-gear" />
              <span className="reality-title">Reality settings</span>
              <span className="reality-summary">capital · sizing · fees &amp; slippage</span>
              <ChevronDown size={14} className={`reality-chev ${realityOpen ? "open" : ""}`} />
            </button>
            {realityOpen && (
              <>
                <div className="reality-grid">
                  <label className="reality-field">
                    <span className="reality-field-label"><Wallet size={12} />Initial Capital</span>
                    <div className="reality-ctl">
                      <input type="number" min={1000} step={1000} value={initialCapital} onChange={(event) => setInitialCapital(Number(event.target.value))} />
                      <span className="reality-suffix">₹</span>
                    </div>
                  </label>
                  <label className="reality-field reality-field-pos">
                    <span className="reality-field-label">
                      <Layers size={12} />Position Size
                      <span className="reality-mode">
                        <button type="button" className={positionSizing === "pct" ? "on" : ""} onClick={(e) => { e.preventDefault(); setPositionSizing("pct"); }}>%</button>
                        <button type="button" className={positionSizing === "fixed" ? "on" : ""} onClick={(e) => { e.preventDefault(); setPositionSizing("fixed"); }}>#</button>
                      </span>
                    </span>
                    <div className="reality-ctl">
                      <input type="number" min={0.1} step={1} value={positionSize} onChange={(event) => setPositionSize(Number(event.target.value))} />
                      <span className="reality-suffix">{positionSizing === "pct" ? "% per trade" : "units"}</span>
                    </div>
                  </label>
                  <label className="reality-field">
                    <span className="reality-field-label"><Receipt size={12} />Brokerage / order</span>
                    <select value={brokerage} disabled={market !== "IN"} onChange={(event) => setBrokerage(Number(event.target.value))}>
                      <option value={0}>₹0 (free)</option>
                      <option value={20}>₹20 (discount)</option>
                      <option value={50}>₹50 (full)</option>
                    </select>
                  </label>
                  <label className="reality-field">
                    <span className="reality-field-label"><Gauge size={12} />Slippage</span>
                    <div className="reality-ctl">
                      <input type="number" min={0} step={0.01} value={slippagePct} onChange={(event) => setSlippagePct(Number(event.target.value))} />
                      <span className="reality-suffix">%</span>
                    </div>
                  </label>
                </div>
                <div className="reality-pills">
                  <span className="reality-pill">Indian brokerage + STT + GST</span>
                  <span className="reality-pill">Past results are not guarantees</span>
                </div>
              </>
            )}
          </div>

          <div className="editor-toolbar">
            <div className="form-group editor-template">
              <div className="form-label">Starter template</div>
              <select value={templateId} onChange={(event) => chooseTemplate(event.target.value)}>
                {STRATEGY_TEMPLATES.map((template) => <option key={template.id} value={template.id}>{template.label} · {template.description}</option>)}
                <option value="custom" disabled>Custom code</option>
              </select>
            </div>
            <span className="editor-hint">Start with a pattern, then change the rules and test it.</span>
          </div>

          {TEMPLATE_PARAMS[templateId] && (
            <div className="param-inputs">
              {TEMPLATE_PARAMS[templateId].map((field) => (
                <label className="param-field" key={field.key}>
                  <span>{field.label}</span>
                  <div className="param-stepper">
                    <button type="button" aria-label={`Decrease ${field.label}`} onClick={() => stepParam(field.key, -1)}>−</button>
                    <input
                      type="number"
                      min={1}
                      value={strategyParams[field.key] ?? field.defaultValue}
                      onChange={(event) => setStrategyParams((prev) => ({ ...prev, [field.key]: Math.max(1, Number(event.target.value)) }))}
                    />
                    <button type="button" aria-label={`Increase ${field.label}`} onClick={() => stepParam(field.key, 1)}>+</button>
                  </div>
                </label>
              ))}
            </div>
          )}

          <div className="code-editor">
            <pre className="code-gutter" aria-hidden="true" ref={gutterRef}>{Array.from({ length: (code.match(/\n/g)?.length ?? 0) + 1 }, (_, i) => i + 1).join("\n")}</pre>
            <textarea
              rows={12}
              spellCheck={false}
              value={code}
              onChange={(e) => { setCode(e.target.value); setTemplateId("custom"); }}
              onScroll={(e) => { const t = e.currentTarget; if (gutterRef.current) gutterRef.current.scrollTop = t.scrollTop; }}
            />
          </div>

          <div className="row" style={{ marginTop: 12 }}>
            <button className="btn-run" onClick={onRun} disabled={running || !symbol}>
              {running ? "Running…" : "▶ Run Backtest"}
            </button>
            {token && (
              <button className="btn-secondary" onClick={onReplay}>
                Replay to Paper
              </button>
            )}
            {token ? (
              <button className="btn-secondary" onClick={onSave}>
                Save Strategy
              </button>
            ) : (
              <span className="save-login-note text-sm">Login to save strategies</span>
            )}
          </div>
          {replayMsg && <p className="success-msg text-sm" style={{ marginTop: 10 }}>{replayMsg}</p>}
          {error && <p className="error-msg" style={{ marginTop: 10 }}>{error}</p>}
        </aside>
      </div>
    </div>
  );
}
