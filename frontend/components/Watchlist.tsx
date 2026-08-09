"use client";

import { useEffect, useState } from "react";
import {
  API_URL,
  MARKETS,
  MARKET_LABELS,
  type Market,
  type User,
} from "@/lib/api";

interface WatchlistsData {
  lists: Record<string, string[]>;
}

async function fetchWatchlist(token: string): Promise<WatchlistsData> {
  const resp = await fetch(`${API_URL}/api/watchlists`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error(String(resp.status));
  return resp.json();
}

async function addToWatchlist(token: string, market: string, symbol: string): Promise<WatchlistsData> {
  const resp = await fetch(`${API_URL}/api/watchlists/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ market, symbol }),
  });
  if (!resp.ok) throw new Error(String(resp.status));
  return resp.json();
}

async function removeFromWatchlist(token: string, market: string, symbol: string): Promise<WatchlistsData> {
  const resp = await fetch(`${API_URL}/api/watchlists/remove`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ market, symbol }),
  });
  if (!resp.ok) throw new Error(String(resp.status));
  return resp.json();
}

export default function Watchlist({ token, user, onPick }: {
  token: string | null;
  user: User | null;
  onPick?: (market: Market, symbol: string) => void;
}) {
  const [lists, setLists] = useState<Record<string, string[]>>({});
  const [error, setError] = useState("");
  const [addSymbol, setAddSymbol] = useState("");
  const [addMarket, setAddMarket] = useState<Market>("IN");

  async function refresh() {
    if (!token) return;
    try {
      const data = await fetchWatchlist(token);
      setLists(data.lists || {});
      setError("");
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  useEffect(() => { refresh(); }, [token]);

  async function onAdd() {
    if (!token || !addSymbol.trim()) return;
    try {
      const data = await addToWatchlist(token, addMarket, addSymbol.trim().toUpperCase());
      setLists(data.lists || {});
      setAddSymbol("");
      setError("");
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  async function onRemove(market: string, symbol: string) {
    if (!token) return;
    try {
      const data = await removeFromWatchlist(token, market, symbol);
      setLists(data.lists || {});
      setError("");
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  if (!token) {
    return (
      <section className="card">
        <h2>Watchlist</h2>
        <p className="muted">Watchlist ke liye login karo.</p>
      </section>
    );
  }

  const totalSymbols = Object.values(lists).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <section className="card">
      <h2>Watchlist {totalSymbols > 0 ? `(${totalSymbols})` : ""}</h2>
      <div className="controls">
        <label>
          Market
          <select value={addMarket} onChange={(e) => setAddMarket(e.target.value as Market)}>
            {MARKETS.map((m) => (<option key={m} value={m}>{MARKET_LABELS[m]}</option>))}
          </select>
        </label>
        <label>
          Symbol
          <input value={addSymbol} onChange={(e) => setAddSymbol(e.target.value)} placeholder="AAPL / RELIANCE" />
        </label>
        <button onClick={onAdd}>Add</button>
      </div>
      {error && <p className="error small">{error}</p>}

      {MARKETS.map((market) => {
        const symbols = lists[market];
        if (!symbols || symbols.length === 0) return null;
        return (
          <div key={market} className="watchlist-group">
            <h3>{market}</h3>
            <div className="scan-list">
              {symbols.map((sym) => (
                <div key={sym} className="scan-chip">
                  <button className="small ghost" onClick={() => onPick?.(market, sym)}>
                    {sym}
                  </button>
                  <button className="small ghost" onClick={() => onRemove(market, sym)}>✕</button>
                </div>
              ))}
            </div>
          </div>
        );
      })}
      {totalSymbols === 0 && <p className="muted small">Koi watchlist symbol nahi. Upar se add karo.</p>}
    </section>
  );
}
