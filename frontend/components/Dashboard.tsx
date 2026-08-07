"use client";

import { useEffect, useState } from "react";
import Chart from "@/components/Chart";
import {
  assistantChat,
  assistantConfirm,
  csvExportUrl,
  getOhlcv,
  getSymbols,
  runBacktest,
  saveStrategy,
  MARKETS,
  type BacktestResult,
  type Bar,
  type Market,
  type SymbolInfo,
  type User,
} from "@/lib/api";

const DEFAULT_CODE = `# signals: 1 = long, 0 = flat, -1 = short
# available: data (open/high/low/close/volume), params, pd, np
fast = params.get("fast", 20)
slow = params.get("slow", 50)
ma_fast = data["close"].rolling(fast).mean()
ma_slow = data["close"].rolling(slow).mean()
signals = (ma_fast > ma_slow).astype(int).diff().fillna(0)`;

export default function Dashboard({ token, user }: { token: string | null; user: User | null }) {
  const [market, setMarket] = useState<Market>("IN");
  const [symbols, setSymbols] = useState<SymbolInfo[]>([]);
  const [symbol, setSymbol] = useState("");
  const [bars, setBars] = useState<Bar[]>([]);
  const [ohlcvError, setOhlcvError] = useState("");
  const [code, setCode] = useState(DEFAULT_CODE);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [aiOpen, setAiOpen] = useState(false);
  const [aiMessage, setAiMessage] = useState("");
  const [aiReply, setAiReply] = useState<{ text: string; needs_confirmation: boolean } | null>(null);
  const [aiError, setAiError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setSymbols([]);
    setSymbol("");
    setBars([]);
    setResult(null);
    getSymbols(market)
      .then((s) => {
        if (cancelled) return;
        setSymbols(s);
        setSymbol(s[0]?.symbol ?? "");
      })
      .catch((e) => setOhlcvError(String(e.message ?? e)));
    return () => {
      cancelled = true;
    };
  }, [market]);

  useEffect(() => {
    if (!symbol) return;
    let cancelled = false;
    setBars([]);
    setOhlcvError("");
    getOhlcv(market, symbol)
      .then((r) => {
        if (cancelled) return;
        setBars(r.bars);
      })
      .catch((e) => setOhlcvError(String(e.message ?? e)));
    return () => {
      cancelled = true;
    };
  }, [market, symbol]);

  async function onRun() {
    setRunning(true);
    setError("");
    setResult(null);
    try {
      const res = await runBacktest({
        market,
        symbol,
        interval: "1d",
        start: "2019-01-01",
        end: new Date().toISOString().slice(0, 10),
        code,
        params: {},
        initial_capital: 100000,
        position_sizing: "pct",
        position_size: 10,
      });
      setResult(res);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setRunning(false);
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

  async function onAsk() {
    setAiError("");
    setAiReply(null);
    try {
      const reply = await assistantChat(aiMessage, token!);
      setAiReply({ text: reply.text, needs_confirmation: reply.needs_confirmation });
      setAiMessage("");
    } catch (e) {
      setAiError(String((e as Error).message ?? e));
    }
  }

  async function onConfirm() {
    setAiError("");
    try {
      await assistantConfirm("run backtest with generated strategy");
      setAiReply((r) => (r ? { ...r, needs_confirmation: false } : r));
    } catch (e) {
      setAiError(String((e as Error).message ?? e));
    }
  }

  const m = result?.metrics;

  return (
    <>
      <section className="controls">
        <label>
          Market
          <select value={market} onChange={(e) => setMarket(e.target.value as Market)}>
            {MARKETS.map((mk) => (
              <option key={mk} value={mk}>
                {mk}
              </option>
            ))}
          </select>
        </label>
        <label>
          Symbol
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {symbols.map((s) => (
              <option key={s.symbol} value={s.symbol}>
                {s.symbol}
              </option>
            ))}
          </select>
        </label>
        {symbol && (
          <a className="csv-link" href={csvExportUrl(market, symbol)}>
            ⬇ CSV export
          </a>
        )}
      </section>

      <section className="chart">
        {ohlcvError && <p className="error">{ohlcvError}</p>}
        <Chart bars={bars} />
      </section>

      <section className="backtest">
        <div className="backtest-form">
          <label>
            Strategy code
            <textarea rows={12} spellCheck={false} value={code} onChange={(e) => setCode(e.target.value)} />
          </label>
          <div className="row">
            <button onClick={onRun} disabled={running || !symbol}>
              {running ? "Running..." : "Run Backtest"}
            </button>
            {token ? (
              <button className="ghost" onClick={onSave}>
                Save Strategy (Pro)
              </button>
            ) : (
              <span className="muted small">Login to save strategies</span>
            )}
          </div>
          {error && <p className="error">{error}</p>}
        </div>

        {result && (
          <div className="result">
            <h2>
              {result.symbol} · {result.interval} · {result.start} → {result.end}
            </h2>
            <code className="hash">run_hash {result.run_hash}</code>
            {m && (
              <div className="metrics">
                <div><span>Return</span><b>{m.total_return_pct.toFixed(2)}%</b></div>
                <div><span>CAGR</span><b>{m.cagr_pct.toFixed(2)}%</b></div>
                <div><span>Sharpe</span><b>{m.sharpe.toFixed(2)}</b></div>
                <div><span>Max DD</span><b>{m.max_drawdown_pct.toFixed(2)}%</b></div>
                <div><span>Win rate</span><b>{m.win_rate_pct.toFixed(2)}%</b></div>
                <div><span>Profit factor</span><b>{m.profit_factor === null ? "∞" : m.profit_factor.toFixed(2)}</b></div>
                <div><span>Trades</span><b>{m.total_trades}</b></div>
              </div>
            )}
            {result.trades.length > 0 && (
              <table>
                <thead>
                  <tr><th>time</th><th>side</th><th>qty</th><th>price</th><th>pnl</th></tr>
                </thead>
                <tbody>
                  {result.trades.map((t) => (
                    <tr key={t.order_id}>
                      <td>{t.timestamp.slice(0, 10)}</td>
                      <td className={t.side === "BUY" ? "buy" : "sell"}>{t.side}</td>
                      <td>{t.qty}</td>
                      <td>{t.price.toFixed(2)}</td>
                      <td className={t.pnl >= 0 ? "buy" : "sell"}>{t.pnl.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </section>

      <section className="assistant">
        <button className="small" onClick={() => setAiOpen(!aiOpen)}>
          🤖 AI Assistant {user?.plan === "pro" ? "" : "(Pro)"}
        </button>
        {aiOpen && (
          <div className="assistant-panel">
            <div className="row">
              <input
                placeholder='Ask in Hinglish: "RSI samjhao" ya "buy above sma20 strategy banao"'
                value={aiMessage}
                onChange={(e) => setAiMessage(e.target.value)}
                disabled={!token}
              />
              <button className="small" onClick={onAsk} disabled={!token || !aiMessage}>
                Ask
              </button>
            </div>
            {!token && <p className="muted small">Pro login required for the AI assistant.</p>}
            {aiError && <p className="error">{aiError}</p>}
            {aiReply && (
              <div className="ai-reply">
                <pre className="small">{aiReply.text}</pre>
                {aiReply.needs_confirmation && (
                  <button className="small" onClick={onConfirm}>
                    ✅ Confirm — run backtest with this strategy
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </section>
    </>
  );
}
