"use client";

import { useEffect, useRef, useState } from "react";
import {
  getAccount,
  getHistory,
  getPositions,
  placeOrder,
  checkExits,
  resetAccount,
  setLevels,
  MARKETS,
  MARKET_LABELS,
  type Account,
  type Market,
  type Order,
  type OrderType,
  type Position,
  type Trade,
  type User,
} from "@/lib/api";
import PaperChart from "./PaperChart";

export default function Paper({ token, user }: { token: string | null; user: User | null }) {
  const [market, setMarket] = useState<Market>("IN");
  const [symbol, setSymbol] = useState("RELIANCE");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [qty, setQty] = useState(10);
  const [orderType, setOrderType] = useState<OrderType>("MARKET");
  const [price, setPrice] = useState("");
  const [stopPrice, setStopPrice] = useState("");
  const [sl, setSl] = useState("");
  const [tp, setTp] = useState("");
  const [account, setAccount] = useState<Account | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [history, setHistory] = useState<Trade[]>([]);
  const [lastOrder, setLastOrder] = useState<Order | null>(null);
  const [exitOrders, setExitOrders] = useState<Order[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    if (!token) return;
    const [acc, pos, hist] = await Promise.all([
      getAccount(token, market),
      getPositions(token, market),
      getHistory(token),
    ]);
    setAccount(acc);
    setPositions(pos);
    setHistory(hist);
  }

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message ?? e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, market]);

  useEffect(() => {
    if (!token) return;
    const id = setInterval(() => {
      refresh().catch(() => {});
    }, 5000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, market]);

  const onResetRef = useRef<() => void>(() => {});
  onResetRef.current = onReset;

  useEffect(() => {
    const onResetEvent = () => {
      onResetRef.current();
    };
    window.addEventListener("tf:paper-reset", onResetEvent);
    return () => window.removeEventListener("tf:paper-reset", onResetEvent);
  }, []);

  const needsPrice = orderType === "LIMIT" || orderType === "STOP_LIMIT" || orderType === "BRACKET";
  const needsStop = orderType === "STOP" || orderType === "STOP_LIMIT" || orderType === "SL" || orderType === "SL-M";
  const needsBracket = orderType === "BRACKET";

  async function onPlace(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setBusy(true);
    setError("");
    setLastOrder(null);
    try {
      const order = await placeOrder({
        market,
        symbol,
        side,
        qty,
        order_type: orderType,
        price: price ? Number(price) : null,
        stop_price: stopPrice ? Number(stopPrice) : null,
        sl: sl ? Number(sl) : null,
        tp: tp ? Number(tp) : null,
      }, token);
      setLastOrder(order);
      await refresh();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    } finally {
      setBusy(false);
    }
  }

  async function onCheckExits() {
    if (!token) return;
    setBusy(true);
    setError("");
    setExitOrders([]);
    try {
      const prices: Record<string, number> = {};
      positions.forEach((p) => {
        prices[p.symbol] = p.ltp;
      });
      const res = await checkExits(market, prices, token);
      setExitOrders(res.orders);
      await refresh();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    } finally {
      setBusy(false);
    }
  }

  async function onReset() {
    if (!token) return;
    setError("");
    try {
      const amtText = window.prompt(
        "Reset balance to:",
        String(account?.balance ?? 100000)
      );
      const amount = amtText ? Number(amtText) : NaN;
      const acc = Number.isFinite(amount) && amount > 0 ? amount : undefined;
      const res = await resetAccount(token, market, acc);
      setAccount(res);
      setPositions([]);
      setHistory([]);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  }

  async function onLevelsChanged(sl: number | null, tp: number | null) {
    if (!token) return;
    setError("");
    try {
      await setLevels(token, market, symbol, sl, tp);
      await refresh();
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  }

  async function onClose() {
    const p = positions.find((x) => x.symbol === symbol);
    if (!token || !p) return;
    setBusy(true);
    setError("");
    setLastOrder(null);
    try {
      const order = await placeOrder(
        {
          market,
          symbol,
          side: p.qty > 0 ? "SELL" : "BUY",
          qty: Math.abs(p.qty),
          order_type: "MARKET",
        },
        token
      );
      setLastOrder(order);
      await refresh();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    } finally {
      setBusy(false);
    }
  }

  async function onReverse() {
    const p = positions.find((x) => x.symbol === symbol);
    if (!token || !p) return;
    setBusy(true);
    setError("");
    setLastOrder(null);
    try {
      await placeOrder(
        {
          market,
          symbol,
          side: p.qty > 0 ? "SELL" : "BUY",
          qty: Math.abs(p.qty),
          order_type: "MARKET",
        },
        token
      );
      const order = await placeOrder(
        {
          market,
          symbol,
          side: p.qty > 0 ? "BUY" : "SELL",
          qty: Math.abs(p.qty),
          order_type: "MARKET",
        },
        token
      );
      setLastOrder(order);
      await refresh();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {!token && <p className="muted small">Login required to use the paper trading account.</p>}
      <section className="controls">
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
          <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
        </label>
        <button className="small ghost" onClick={onReset} disabled={!token}>Reset account</button>
      </section>

      {account && (
        <section className="metrics account">
          <div><span>Balance</span><b>{account.balance.toFixed(2)}</b></div>
          <div><span>Equity</span><b>{account.equity.toFixed(2)}</b></div>
          <div><span>Positions</span><b>{positions.length}</b></div>
        </section>
      )}

      <section className="backtest-form">
        <form className="order-form" onSubmit={onPlace}>
          <div className="row">
            <label>
              Side
              <select value={side} onChange={(e) => setSide(e.target.value as "BUY" | "SELL")}>
                <option>BUY</option>
                <option>SELL</option>
              </select>
            </label>
            <label>
              Qty
              <input type="number" min={1} value={qty} onChange={(e) => setQty(Number(e.target.value))} />
            </label>
            <label>
              Type
              <select value={orderType} onChange={(e) => setOrderType(e.target.value as OrderType)}>
                <option>MARKET</option>
                <option>LIMIT</option>
                <option>SL</option>
                <option>SL-M</option>
                <option>STOP</option>
                <option>STOP_LIMIT</option>
                <option>BRACKET</option>
              </select>
            </label>
            {needsPrice && (
              <label>
                {orderType === "BRACKET" ? "Entry price" : "Price"}
                <input type="number" value={price} onChange={(e) => setPrice(e.target.value)} />
              </label>
            )}
            {needsStop && (
              <label>
                Stop price
                <input type="number" value={stopPrice} onChange={(e) => setStopPrice(e.target.value)} />
              </label>
            )}
            {needsBracket && (
              <>
                <label>
                  SL
                  <input type="number" value={sl} onChange={(e) => setSl(e.target.value)} />
                </label>
                <label>
                  TP
                  <input type="number" value={tp} onChange={(e) => setTp(e.target.value)} />
                </label>
              </>
            )}
          </div>
          <div className="row">
            <button type="submit" disabled={busy || !token}>
              {busy ? "Placing..." : `Place ${side} ${orderType}`}
            </button>
            <button type="button" className="small ghost" onClick={onCheckExits} disabled={busy || !token || positions.length === 0}>
              Run exits
            </button>
            {lastOrder && (
              <span className={`muted small ${lastOrder.status === "FILLED" ? "buy" : lastOrder.status === "REJECTED" ? "sell" : ""}`}>
                {lastOrder.status}
                {lastOrder.filled_price != null ? ` @ ${lastOrder.filled_price.toFixed(2)}` : ""}
                {lastOrder.status === "REJECTED" && " (rejected)"}
              </span>
            )}
          </div>
          {error && <p className="error">{error}</p>}
        </form>
      </section>

      {exitOrders.length > 0 && (
        <section className="result">
          <h2>Exits triggered ({exitOrders.length})</h2>
          <table>
            <thead>
              <tr><th>symbol</th><th>side</th><th>qty</th><th>price</th><th>status</th></tr>
            </thead>
            <tbody>
              {exitOrders.map((o) => (
                <tr key={o.id}>
                  <td>{o.symbol}</td>
                  <td>{o.side}</td>
                  <td>{o.qty}</td>
                  <td>{o.filled_price != null ? o.filled_price.toFixed(2) : "—"}</td>
                  <td>{o.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section className="result">
        <h2>
          Position chart <span className="muted small">· {symbol}</span>
          <span className="muted small"> · drag SL/TP lines · right-click to close/reverse</span>
        </h2>
        <PaperChart
          market={market}
          symbol={symbol}
          position={positions.find((p) => p.symbol === symbol) ?? null}
          onLevelsChanged={onLevelsChanged}
          onClose={onClose}
          onReverse={onReverse}
        />
      </section>

      {positions.length > 0 && (
        <section className="result">
          <h2>Positions</h2>
          <table>
            <thead>
              <tr><th>symbol</th><th>qty</th><th>avg</th><th>ltp</th><th>SL</th><th>TP</th><th>unrealized</th></tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.symbol}>
                  <td>{p.symbol}</td>
                  <td>{p.qty}</td>
                  <td>{p.avg_price.toFixed(2)}</td>
                  <td>{p.ltp.toFixed(2)}</td>
                  <td>{p.sl != null ? p.sl.toFixed(2) : "—"}</td>
                  <td>{p.tp != null ? p.tp.toFixed(2) : "—"}</td>
                  <td className={p.unrealized_pnl >= 0 ? "buy" : "sell"}>{p.unrealized_pnl.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {history.length > 0 && (
        <section className="result">
          <h2>Closed trades</h2>
          <table>
            <thead>
              <tr><th>time</th><th>symbol</th><th>side</th><th>qty</th><th>price</th><th>pnl</th></tr>
            </thead>
            <tbody>
              {history.map((t) => (
                <tr key={t.order_id}>
                  <td>{t.timestamp.slice(0, 10)}</td>
                  <td>{t.symbol}</td>
                  <td className={t.side === "BUY" ? "buy" : "sell"}>{t.side}</td>
                  <td>{t.qty}</td>
                  <td>{t.price.toFixed(2)}</td>
                  <td className={t.pnl >= 0 ? "buy" : "sell"}>{t.pnl.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </>
  );
}
