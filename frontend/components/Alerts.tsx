"use client";

import { useEffect, useState } from "react";
import {
  checkAlerts,
  clearAlertNotifications,
  createAlert,
  deleteAlert,
  listAlertNotifications,
  listAlerts,
  MARKETS,
  type AlertNotification,
  type AlertRule,
  type Market,
  type User,
} from "@/lib/api";

export default function Alerts({ token, user }: { token: string | null; user: User | null }) {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [notifications, setNotifications] = useState<AlertNotification[]>([]);
  const [symbol, setSymbol] = useState("");
  const [market, setMarket] = useState<Market>("IN");
  const [metric, setMetric] = useState<"PRICE" | "RSI">("PRICE");
  const [condition, setCondition] = useState<"ABOVE" | "BELOW">("ABOVE");
  const [value, setValue] = useState(100);
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);

  async function refresh() {
    if (!token) return;
    setError("");
    try {
      setRules(await listAlerts(token));
      setNotifications(await listAlertNotifications(token));
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function onCreate() {
    if (!token) return;
    setError("");
    try {
      await createAlert(token, { symbol: symbol.trim().toUpperCase(), market, metric, condition, value });
      setSymbol("");
      await refresh();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  async function onDelete(ruleId: string) {
    if (!token) return;
    setError("");
    try {
      await deleteAlert(token, ruleId);
      await refresh();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  async function onCheck() {
    if (!token) return;
    setChecking(true);
    setError("");
    try {
      const res = await checkAlerts(token);
      await refresh();
      if (res.triggered > 0) setError(`${res.triggered} alert(s) triggered!`);
    } catch (err) {
      setError(String((err as Error).message ?? err));
    } finally {
      setChecking(false);
    }
  }

  async function onClear() {
    if (!token) return;
    setError("");
    try {
      await clearAlertNotifications(token);
      setNotifications([]);
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  if (!token) {
    return (
      <section className="card">
        <h2>Alerts</h2>
        <p className="muted">Alerts ke liye login karo (free users ke liye bhi available).</p>
      </section>
    );
  }

  return (
    <section className="card">
      <h2>Alerts {user ? `(${user.email})` : ""}</h2>

      <div className="controls">
        <label>
          Symbol
          <input value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="AAPL / BTCUSDT / RELIANCE" />
        </label>
        <label>
          Market
          <select value={market} onChange={(e) => setMarket(e.target.value as Market)}>
            {MARKETS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </label>
        <label>
          Metric
          <select value={metric} onChange={(e) => setMetric(e.target.value as "PRICE" | "RSI")}>
            <option value="PRICE">Price</option>
            <option value="RSI">RSI (14)</option>
          </select>
        </label>
        <label>
          Condition
          <select value={condition} onChange={(e) => setCondition(e.target.value as "ABOVE" | "BELOW")}>
            <option value="ABOVE">Above (upar)</option>
            <option value="BELOW">Below (neeche)</option>
          </select>
        </label>
        <label>
          Target value
          <input type="number" step="0.01" value={value} onChange={(e) => setValue(Number(e.target.value))} />
        </label>
        <button onClick={onCreate}>Add Alert</button>
        <button onClick={onCheck} disabled={checking}>
          {checking ? "Checking..." : "Check now"}
        </button>
      </div>
      {error && <p className="error small">{error}</p>}

      <h3>My rules ({rules.length})</h3>
      {rules.length === 0 && <p className="muted small">Koi alert rule nahi. Upar ek banaiye.</p>}
      {rules.map((r) => (
        <div className="journal-card" key={r.rule_id}>
          <div className="row">
            <b>{r.symbol}</b>
            <span className={`small ${r.active ? "buy" : "muted"}`}>
              {r.metric} {r.condition} {r.value} · {r.active ? "active" : "fired"}
            </span>
            <button className="small ghost" onClick={() => onDelete(r.rule_id)}>✕</button>
          </div>
        </div>
      ))}

      <h3>Notifications ({notifications.length})</h3>
      {notifications.length === 0 && <p className="muted small">Abhi tak koi notification nahi.</p>}
      {notifications.map((n) => (
        <div className="journal-card" key={n.id}>
          <p className="small">{n.message}</p>
          <span className="muted small">{n.created_at?.slice(0, 19)}</span>
        </div>
      ))}
      {notifications.length > 0 && (
        <button className="small ghost" onClick={onClear}>Clear notifications</button>
      )}
    </section>
  );
}
