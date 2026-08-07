"use client";

import { useEffect, useState } from "react";
import {
  getAccount,
  getHistory,
  getPositions,
  placeOrder,
  resetAccount,
  MARKETS,
  type Account,
  type Market,
  type Order,
  type Position,
  type Trade,
} from "@/lib/api";

const USER_ID = "demo";

export default function Paper() {
  const [market, setMarket] = useState<Market>("IN");
  const [symbol, setSymbol] = useState("RELIANCE");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [qty, setQty] = useState(10);
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [price, setPrice] = useState("");
  const [account, setAccount] = useState<Account | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [history, setHistory] = useState<Trade[]>([]);
  const [lastOrder, setLastOrder] = useState<Order | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [acc, pos, hist] = await Promise.all([
      getAccount(USER_ID, market),
      getPositions(USER_ID, market),
      getHistory(USER_ID),
    ]);
    setAccount(acc);
    setPositions(pos);
    setHistory(hist);
  }

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message ?? e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [market]);

  async function onPlace(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setLastOrder(null);
    try {
      const order = await placeOrder({
        user_id: USER_ID,
        market,
        symbol,
        side,
        qty,
        order_type: orderType,
        price: orderType === "LIMIT" ? Number(price) : null,
      });
      setLastOrder(order);
      await refresh();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    } finally {
      setBusy(false);
    }
  }

  async function onReset() {
    setError("");
    try {
      const acc = await resetAccount(USER_ID, market);
      setAccount(acc);
      setPositions([]);
      setHistory([]);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  }

  return (
    <>
      <section className="controls">
        <label>
          Market
          <select value={market} onChange={(e) => setMarket(e.target.value as Market)}>
            {MARKETS.map((mk) => (
              <option key={mk} value={mk}>{mk}</option>
            ))}
          </select>
        </label>
        <label>
          Symbol
          <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
        </label>
        <button className="small ghost" onClick={onReset}>Reset account</button>
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
              <select value={orderType} onChange={(e) => setOrderType(e.target.value as "MARKET" | "LIMIT")}>
                <option>MARKET</option>
                <option>LIMIT</option>
              </select>
            </label>
            {orderType === "LIMIT" && (
              <label>
                Limit price
                <input type="number" value={price} onChange={(e) => setPrice(e.target.value)} />
              </label>
            )}
          </div>
          <div className="row">
            <button type="submit" disabled={busy}>
              {busy ? "Placing..." : `Place ${side} ${orderType}`}
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

      {positions.length > 0 && (
        <section className="result">
          <h2>Positions</h2>
          <table>
            <thead>
              <tr><th>symbol</th><th>qty</th><th>avg</th><th>ltp</th><th>unrealized</th></tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.symbol}>
                  <td>{p.symbol}</td>
                  <td>{p.qty}</td>
                  <td>{p.avg_price.toFixed(2)}</td>
                  <td>{p.ltp.toFixed(2)}</td>
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
