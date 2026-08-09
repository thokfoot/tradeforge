"use client";

import { useEffect, useState } from "react";
import {
  builderGenerate,
  getSymbols,
  MARKETS,
  MARKET_LABELS,
  runBacktest,
  type BacktestResult,
  type BuilderCondition,
  type Market,
  type SymbolInfo,
  type User,
} from "@/lib/api";

const INDICATORS = ["close", "open", "high", "low", "volume", "sma", "ema", "rsi"];
const MA_INDICATORS = ["sma", "ema", "rsi"];

function blankCondition(): BuilderCondition {
  return { indicator: "close", period: null, op: "above", ref: null, ref_period: null, value: 100 };
}

function startDateFor(interval: string): string {
  const days = interval === "1m" ? 7 : interval === "1h" ? 60 : 2191;
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export default function Builder({ token, user }: { token: string | null; user: User | null }) {
  const [name, setName] = useState("My strategy");
  const [entryOp, setEntryOp] = useState<"AND" | "OR">("AND");
  const [entryConds, setEntryConds] = useState<BuilderCondition[]>([]);
  const [exitOp, setExitOp] = useState<"AND" | "OR">("OR");
  const [exitConds, setExitConds] = useState<BuilderCondition[]>([]);
  const [code, setCode] = useState<string | null>(null);
  const [genErrors, setGenErrors] = useState<string[]>([]);
  const [genWarnings, setGenWarnings] = useState<string[]>([]);
  const [genError, setGenError] = useState("");

  const [market, setMarket] = useState<Market>("IN");
  const [symbols, setSymbols] = useState<SymbolInfo[]>([]);
  const [symbol, setSymbol] = useState("");
  const [interval, setInterval] = useState("1d");
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setSymbols([]);
    setSymbol("");
    getSymbols(market)
      .then((s) => {
        if (cancelled) return;
        setSymbols(s);
        setSymbol(s[0]?.symbol ?? "");
      })
      .catch((e) => setRunError(String(e.message ?? e)));
    return () => {
      cancelled = true;
    };
  }, [market]);

  function updateCond(
    setter: React.Dispatch<React.SetStateAction<BuilderCondition[]>>,
    index: number,
    patch: Partial<BuilderCondition>
  ) {
    setter((prev) => prev.map((c, i) => (i === index ? { ...c, ...patch } : c)));
  }

  async function onGenerate() {
    setGenError("");
    setGenErrors([]);
    setGenWarnings([]);
    setCode(null);
    try {
      const res = await builderGenerate(token!, {
        name,
        entry: { op: entryOp, conditions: entryConds },
        exit: { op: exitOp, conditions: exitConds },
      });
      setCode(res.code);
      setGenErrors(res.errors);
      setGenWarnings(res.warnings);
      if (!res.valid) setGenError("Generated code failed validation (see errors).");
    } catch (err) {
      setGenError(String((err as Error).message ?? err));
    }
  }

  async function onRun() {
    if (!code) return;
    setRunning(true);
    setRunError("");
    setResult(null);
    try {
      const res = await runBacktest({
        market,
        symbol,
        interval,
        start: startDateFor(interval),
        end: new Date().toISOString().slice(0, 10),
        code,
        params: {},
        initial_capital: 100000,
        position_sizing: "pct",
        position_size: 10,
      });
      setResult(res);
    } catch (err) {
      setRunError(String((err as Error).message ?? err));
    } finally {
      setRunning(false);
    }
  }

  function renderRule(
    label: string,
    op: "AND" | "OR",
    setOp: (v: "AND" | "OR") => void,
    conds: BuilderCondition[],
    setConds: React.Dispatch<React.SetStateAction<BuilderCondition[]>>
  ) {
    return (
      <div className="result">
        <h2>{label}</h2>
        <label className="check">
          Join
          <select value={op} onChange={(e) => setOp(e.target.value as "AND" | "OR")}>
            <option value="AND">AND (sab conditions)</option>
            <option value="OR">OR (koi ek)</option>
          </select>
        </label>
        {conds.map((c, i) => (
          <div className="row" key={i}>
            <select
              value={c.indicator}
              onChange={(e) => updateCond(setConds, i, { indicator: e.target.value })}
            >
              {INDICATORS.map((ind) => (
                <option key={ind} value={ind}>{ind}</option>
              ))}
            </select>
            {MA_INDICATORS.includes(c.indicator) && (
              <input
                type="number"
                style={{ width: 70 }}
                value={c.period ?? 14}
                onChange={(e) => updateCond(setConds, i, { period: Number(e.target.value) })}
              />
            )}
            <select
              value={c.op}
              onChange={(e) => updateCond(setConds, i, { op: e.target.value as "above" | "below" })}
            >
              <option value="above">above (upar)</option>
              <option value="below">below (neeche)</option>
            </select>
            <select
              value={c.ref ?? "value"}
              onChange={(e) => {
                const v = e.target.value;
                updateCond(setConds, i, { ref: v === "value" ? null : v, ref_period: null });
              }}
            >
              <option value="value">value (number)</option>
              {INDICATORS.map((ind) => (
                <option key={ind} value={ind}>vs {ind}</option>
              ))}
            </select>
            {c.ref == null ? (
              <input
                type="number"
                step="0.01"
                style={{ width: 90 }}
                value={c.value ?? 0}
                onChange={(e) => updateCond(setConds, i, { value: Number(e.target.value) })}
              />
            ) : MA_INDICATORS.includes(c.ref) ? (
              <input
                type="number"
                style={{ width: 70 }}
                value={c.ref_period ?? 20}
                onChange={(e) => updateCond(setConds, i, { ref_period: Number(e.target.value) })}
              />
            ) : null}
            <button className="small ghost" onClick={() => setConds(conds.filter((_, j) => j !== i))}>
              ✕
            </button>
          </div>
        ))}
        <button
          className="small"
          onClick={() => setConds([...conds, blankCondition()])}
        >
          + Add condition
        </button>
      </div>
    );
  }

  const m = result?.metrics;

  return (
    <section className="card">
      <h2>No-Code Strategy Builder {user ? `(${user.email})` : ""}</h2>
      {!token ? (
        <p className="muted small">Pro login required for the strategy builder.</p>
      ) : (
        <>
          <label className="check">
            Strategy name
            <input value={name} onChange={(e) => setName(e.target.value)} style={{ width: 220 }} />
          </label>

          {renderRule("BUY when (entry)", entryOp, setEntryOp, entryConds, setEntryConds)}
          {renderRule("SELL when (exit — optional, default: exit jab buy false)", exitOp, setExitOp, exitConds, setExitConds)}

          <div className="row">
            <button onClick={onGenerate}>Generate Strategy</button>
          </div>
          {genError && <p className="error small">{genError}</p>}
          {genErrors.length > 0 && <p className="error small">{genErrors.join("; ")}</p>}
          {genWarnings.length > 0 && <p className="muted small">{genWarnings.join("; ")}</p>}

          {code && (
            <div className="result">
              <h2>Generated code {result?.symbol ? "· validated" : ""}</h2>
              <pre className="small">{code}</pre>

              <div className="controls">
                <label>
                  Market
                  <select value={market} onChange={(e) => setMarket(e.target.value as Market)}>
                    {MARKETS.map((mk) => (
                      <option key={mk} value={mk}>{MARKET_LABELS[mk]}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Symbol
                  <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
                    {symbols.map((s) => (
                      <option key={s.symbol} value={s.symbol}>{s.symbol}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Interval
                  <select value={interval} onChange={(e) => setInterval(e.target.value)}>
                    <option value="1d">1D</option>
                    {market !== "IN" && <option value="1h">1H</option>}
                    {market !== "IN" && <option value="1m">1M</option>}
                  </select>
                </label>
                <button onClick={onRun} disabled={running || !symbol}>
                  {running ? "Running..." : "Run Backtest"}
                </button>
              </div>
              {runError && <p className="error small">{runError}</p>}
              {result && m && (
                <div className="metrics">
                  <div><span>Return</span><b>{m.total_return_pct.toFixed(2)}%</b></div>
                  <div><span>CAGR</span><b>{m.cagr_pct.toFixed(2)}%</b></div>
                  <div><span>Sharpe</span><b>{m.sharpe.toFixed(2)}</b></div>
                  <div><span>Max DD</span><b>{m.max_drawdown_pct.toFixed(2)}%</b></div>
                  <div><span>Win rate</span><b>{m.win_rate_pct.toFixed(2)}%</b></div>
                  <div><span>Trades</span><b>{m.total_trades}</b></div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
}
