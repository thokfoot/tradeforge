"use client";

import { useState } from "react";
import { screenerScan, MARKETS, type Market, type ScreenerRow } from "@/lib/api";

export default function Screener() {
  const [market, setMarket] = useState<Market>("IN");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [minVol, setMinVol] = useState("");
  const [minChg1m, setMinChg1m] = useState("");
  const [aboveSma200, setAboveSma200] = useState(false);
  const [limit, setLimit] = useState(50);
  const [rows, setRows] = useState<ScreenerRow[]>([]);
  const [meta, setMeta] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  async function onScan() {
    setRunning(true);
    setError("");
    setRows([]);
    setMeta("");
    const filters: Record<string, unknown> = {};
    if (minPrice) filters.min_price = Number(minPrice);
    if (maxPrice) filters.max_price = Number(maxPrice);
    if (minVol) filters.min_volume = Number(minVol);
    if (minChg1m) filters.min_change_1m_pct = Number(minChg1m);
    if (aboveSma200) filters.above_sma_200 = true;
    filters.sort_by = "change_1m_pct";
    try {
      const res = await screenerScan(market, filters, limit);
      setRows(res.results);
      setMeta(`scanned ${res.scanned} symbols → ${res.count} matches`);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setRunning(false);
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
        <label>Min price<input type="number" value={minPrice} onChange={(e) => setMinPrice(e.target.value)} /></label>
        <label>Max price<input type="number" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} /></label>
        <label>Min avg vol<input type="number" value={minVol} onChange={(e) => setMinVol(e.target.value)} /></label>
        <label>Min 1m gain %<input type="number" value={minChg1m} onChange={(e) => setMinChg1m(e.target.value)} /></label>
        <label>
          Limit
          <input type="number" value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
        </label>
        <label className="check">
          <input type="checkbox" checked={aboveSma200} onChange={(e) => setAboveSma200(e.target.checked)} />
          Above SMA 200
        </label>
        <button className="small" onClick={onScan} disabled={running}>
          {running ? "Scanning..." : "Scan"}
        </button>
      </section>

      {meta && <p className="muted small">{meta}</p>}
      {error && <p className="error">{error}</p>}

      {rows.length > 0 && (
        <section className="result">
          <table>
            <thead>
              <tr>
                <th>symbol</th><th>close</th><th>1d %</th><th>5d %</th>
                <th>1m %</th><th>3m %</th><th>avg vol</th><th>SMA50</th><th>SMA200</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.symbol}>
                  <td>{r.symbol}</td>
                  <td>{r.last_close.toFixed(2)}</td>
                  <td className={r.change_1d_pct != null && r.change_1d_pct >= 0 ? "buy" : "sell"}>{r.change_1d_pct?.toFixed(2) ?? "—"}</td>
                  <td className={r.change_5d_pct != null && r.change_5d_pct >= 0 ? "buy" : "sell"}>{r.change_5d_pct?.toFixed(2) ?? "—"}</td>
                  <td className={r.change_1m_pct != null && r.change_1m_pct >= 0 ? "buy" : "sell"}>{r.change_1m_pct?.toFixed(2) ?? "—"}</td>
                  <td className={r.change_3m_pct != null && r.change_3m_pct >= 0 ? "buy" : "sell"}>{r.change_3m_pct?.toFixed(2) ?? "—"}</td>
                  <td>{r.avg_volume_20 != null ? Math.round(r.avg_volume_20).toLocaleString() : "—"}</td>
                  <td>{r.above_sma_50 == null ? "—" : r.above_sma_50 ? "✅" : "❌"}</td>
                  <td>{r.above_sma_200 == null ? "—" : r.above_sma_200 ? "✅" : "❌"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </>
  );
}
