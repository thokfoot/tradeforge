"use client";

import { useEffect, useState } from "react";
import {
  deleteScan,
  listScans,
  runSavedScan,
  saveScan,
  screenerScan,
  MARKETS,
  type Market,
  type SavedScan,
  type ScreenerRow,
  type User,
} from "@/lib/api";

export default function Screener({ token, user }: { token: string | null; user: User | null }) {
  const [market, setMarket] = useState<Market>("IN");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [minVol, setMinVol] = useState("");
  const [minChg1m, setMinChg1m] = useState("");
  const [minRsi, setMinRsi] = useState("");
  const [maxRsi, setMaxRsi] = useState("");
  const [minVolRatio, setMinVolRatio] = useState("");
  const [aboveSma20, setAboveSma20] = useState(false);
  const [aboveSma200, setAboveSma200] = useState(false);
  const [macdBull, setMacdBull] = useState(false);
  const [sortBy, setSortBy] = useState("change_1m_pct");
  const [limit, setLimit] = useState(50);
  const [rows, setRows] = useState<ScreenerRow[]>([]);
  const [meta, setMeta] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [scanName, setScanName] = useState("");
  const [scans, setScans] = useState<SavedScan[]>([]);
  const [scanMsg, setScanMsg] = useState("");

  useEffect(() => {
    if (!token) return;
    listScans(token)
      .then(setScans)
      .catch(() => {});
  }, [token]);

  function buildFilters(): Record<string, unknown> {
    const filters: Record<string, unknown> = {};
    if (minPrice) filters.min_price = Number(minPrice);
    if (maxPrice) filters.max_price = Number(maxPrice);
    if (minVol) filters.min_volume = Number(minVol);
    if (minChg1m) filters.min_change_1m_pct = Number(minChg1m);
    if (minRsi) filters.min_rsi = Number(minRsi);
    if (maxRsi) filters.max_rsi = Number(maxRsi);
    if (minVolRatio) filters.min_vol_ratio = Number(minVolRatio);
    if (aboveSma20) filters.above_sma_20 = true;
    if (aboveSma200) filters.above_sma_200 = true;
    if (macdBull) filters.macd_above_signal = true;
    filters.sort_by = sortBy;
    return filters;
  }

  async function onScan() {
    setRunning(true);
    setError("");
    setRows([]);
    setMeta("");
    setScanMsg("");
    try {
      const res = await screenerScan(market, buildFilters(), limit);
      setRows(res.results);
      setMeta(`scanned ${res.scanned} symbols → ${res.count} matches`);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setRunning(false);
    }
  }

  async function onSaveScan() {
    if (!token) return;
    setScanMsg("");
    setError("");
    try {
      await saveScan(scanName, market, buildFilters(), limit, token);
      setScanName("");
      setScans(await listScans(token));
      setScanMsg("Scan saved ✓");
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  }

  async function onRunSaved(scan: SavedScan) {
    if (!token) return;
    setError("");
    setScanMsg("");
    try {
      const res = await runSavedScan(scan.id, token);
      setRows(res.results);
      setMeta(`"${res.name}" → ${res.count} matches`);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  }

  async function onDeleteScan(scan: SavedScan) {
    if (!token) return;
    try {
      await deleteScan(scan.id, token);
      setScans(await listScans(token));
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
        <label>Min price<input type="number" value={minPrice} onChange={(e) => setMinPrice(e.target.value)} /></label>
        <label>Max price<input type="number" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} /></label>
        <label>Min avg vol<input type="number" value={minVol} onChange={(e) => setMinVol(e.target.value)} /></label>
        <label>Min 1m gain %<input type="number" value={minChg1m} onChange={(e) => setMinChg1m(e.target.value)} /></label>
        <label>Min RSI<input type="number" value={minRsi} onChange={(e) => setMinRsi(e.target.value)} /></label>
        <label>Max RSI<input type="number" value={maxRsi} onChange={(e) => setMaxRsi(e.target.value)} /></label>
        <label>Min vol ratio<input type="number" step="0.1" value={minVolRatio} onChange={(e) => setMinVolRatio(e.target.value)} /></label>
        <label>
          Sort by
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="change_1m_pct">1m %</option>
            <option value="change_1d_pct">1d %</option>
            <option value="rsi_14">RSI</option>
            <option value="vol_ratio_20">Vol ratio</option>
            <option value="last_close">Close</option>
          </select>
        </label>
        <label>
          Limit
          <input type="number" value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
        </label>
        <label className="check">
          <input type="checkbox" checked={aboveSma20} onChange={(e) => setAboveSma20(e.target.checked)} />
          Above SMA 20
        </label>
        <label className="check">
          <input type="checkbox" checked={aboveSma200} onChange={(e) => setAboveSma200(e.target.checked)} />
          Above SMA 200
        </label>
        <label className="check">
          <input type="checkbox" checked={macdBull} onChange={(e) => setMacdBull(e.target.checked)} />
          MACD bullish
        </label>
        <button className="small" onClick={onScan} disabled={running}>
          {running ? "Scanning..." : "Scan"}
        </button>
      </section>

      {token && (
        <section className="controls saved-scans">
          <label>
            Scan name
            <input value={scanName} placeholder="e.g. Momentum RSI>60" onChange={(e) => setScanName(e.target.value)} />
          </label>
          <button className="small" onClick={onSaveScan} disabled={!scanName}>
            Save Scan
          </button>
          {scanMsg && <span className="muted small">{scanMsg}</span>}
          {scans.length > 0 && (
            <div className="scan-list">
              {scans.map((s) => (
                <span key={s.id} className="scan-chip">
                  <button className="small" onClick={() => onRunSaved(s)}>
                    ▶ {s.name} ({s.market})
                  </button>
                  <button className="small ghost" onClick={() => onDeleteScan(s)}>
                    ✕
                  </button>
                </span>
              ))}
            </div>
          )}
        </section>
      )}

      {meta && <p className="muted small">{meta}</p>}
      {error && <p className="error">{error}</p>}

      {rows.length > 0 && (
        <section className="result">
          <table>
            <thead>
              <tr>
                <th>symbol</th><th>close</th><th>1d %</th><th>5d %</th>
                <th>1m %</th><th>3m %</th><th>avg vol</th><th>vol ratio</th>
                <th>RSI</th><th>%B</th><th>SMA20</th><th>SMA50</th><th>SMA200</th><th>MACD</th>
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
                  <td>{r.vol_ratio_20 != null ? r.vol_ratio_20.toFixed(2) : "—"}</td>
                  <td className={r.rsi_14 != null && r.rsi_14 >= 70 ? "sell" : r.rsi_14 != null && r.rsi_14 <= 30 ? "buy" : ""}>{r.rsi_14?.toFixed(1) ?? "—"}</td>
                  <td>{r.bb_position != null ? r.bb_position.toFixed(2) : "—"}</td>
                  <td>{r.above_sma_20 == null ? "—" : r.above_sma_20 ? "✅" : "❌"}</td>
                  <td>{r.above_sma_50 == null ? "—" : r.above_sma_50 ? "✅" : "❌"}</td>
                  <td>{r.above_sma_200 == null ? "—" : r.above_sma_200 ? "✅" : "❌"}</td>
                  <td>{r.macd_above_signal == null ? "—" : r.macd_above_signal ? "✅" : "❌"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </>
  );
}
