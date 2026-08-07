"use client";

import { useEffect, useState } from "react";
import {
  addJournalEntry,
  deleteJournal,
  listJournal,
  type JournalEntry,
} from "@/lib/api";

const USER_ID = "demo";

export default function Journal() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [tradeId, setTradeId] = useState("");
  const [symbol, setSymbol] = useState("");
  const [side, setSide] = useState("BUY");
  const [qty, setQty] = useState(0);
  const [pnl, setPnl] = useState(0);
  const [note, setNote] = useState("");
  const [lesson, setLesson] = useState("");
  const [rating, setRating] = useState(3);
  const [tags, setTags] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    setEntries(await listJournal(USER_ID));
  }

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message ?? e)));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await addJournalEntry({
        user_id: USER_ID,
        trade_id: tradeId || `manual-${Date.now()}`,
        note,
        symbol,
        side,
        qty,
        pnl,
        tags: tags ? tags.split(",").map((t) => t.trim()).filter(Boolean) : [],
        rating,
        lesson,
      });
      setNote("");
      setLesson("");
      await refresh();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  async function onDelete(entryId: string) {
    setError("");
    try {
      await deleteJournal(entryId, USER_ID);
      await refresh();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  return (
    <>
      <section className="backtest-form">
        <form className="order-form" onSubmit={onSubmit}>
          <div className="row">
            <label>Trade ID<input value={tradeId} onChange={(e) => setTradeId(e.target.value)} /></label>
            <label>Symbol<input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} /></label>
            <label>
              Side
              <select value={side} onChange={(e) => setSide(e.target.value)}>
                <option>BUY</option>
                <option>SELL</option>
              </select>
            </label>
            <label>Qty<input type="number" value={qty} onChange={(e) => setQty(Number(e.target.value))} /></label>
            <label>PnL ₹<input type="number" value={pnl} onChange={(e) => setPnl(Number(e.target.value))} /></label>
            <label>Rating (1-5)<input type="number" min={1} max={5} value={rating} onChange={(e) => setRating(Number(e.target.value))} /></label>
          </div>
          <label>
            Note
            <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} required />
          </label>
          <div className="row">
            <label>Lesson<input value={lesson} onChange={(e) => setLesson(e.target.value)} /></label>
            <label>Tags (comma sep)<input value={tags} onChange={(e) => setTags(e.target.value)} /></label>
          </div>
          <button type="submit">Save journal entry</button>
          {error && <p className="error">{error}</p>}
        </form>
      </section>

      {entries.length > 0 && (
        <section className="result">
          <h2>Journal ({entries.length})</h2>
          {entries.map((e) => (
            <div className="journal-card" key={e.entry_id}>
              <div className="row">
                <b>{e.symbol || e.trade_id}</b>
                <span className="muted small">{e.created_at?.slice(0, 10)}</span>
                <span className={`small ${e.pnl >= 0 ? "buy" : "sell"}`}>{e.pnl.toFixed(2)}</span>
                <button className="small ghost" onClick={() => onDelete(e.entry_id)}>✕</button>
              </div>
              <p className="small">{e.note}</p>
              {e.lesson && <p className="muted small">lesson: {e.lesson}</p>}
              {e.tags.length > 0 && <p className="muted small">#{e.tags.join(" #")}</p>}
              {e.rating != null && <p className="small">{"⭐".repeat(e.rating)}</p>}
            </div>
          ))}
        </section>
      )}
    </>
  );
}
