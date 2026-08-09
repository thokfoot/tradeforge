"use client";

import { useEffect, useState } from "react";
import {
  deleteScan,
  listScans,
  runSavedScan,
  saveScan,
  screenerScan,
  MARKETS,
  MARKET_LABELS,
  type Market,
  type SavedScan,
  type ScreenerRow,
  type User,
} from "@/lib/api";

function NumberField({ label, value, onChange, step }: {
  label: string; value: string; onChange: (v: string) => void; step?: string;
}) {
  return (
    <div className="form-group">
      <div className="form-label">{label}</div>
      <input type="number" step={step} value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

function CheckField({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="form-group" style={{ flexDirection: "row", alignItems: "center", gap: 6, cursor: "pointer" }}>
      <input type="checkbox" style={{ width: 16, height: 16 }} checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="form-label" style={{ textTransform: "none", letterSpacing: 0 }}>{label}</span>
    </label>
  );
}

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
      <section className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Screener</div>
            <div className="card-subtitle">Filter the market in seconds — {user ? "saved scans sync to your account" : "login to save scans"}</div>
          </div>
          <div className="segmented">
            {MARKETS.map((mk) => (
              <button key={mk} className={market === mk ? "on" : ""} onClick={() => setMarket(mk)}>
                {MARKET_LABELS[mk]}
              </button>
            ))}
          </div>
        </div>

        <div className="controls-card" style={{ padding: 0, border: "none", background: "none", marginBottom: 0 }}>
          <NumberField label="Min price" value={minPrice} onChange={setMinPrice} />
          <NumberField label="Max price" value={maxPrice} onChange={setMaxPrice} />
          <NumberField label="Min avg vol" value={minVol} onChange={setMinVol} />
          <NumberField label="Min 1m gain %" value={minChg1m} onChange={setMinChg1m} />
          <NumberField label="Min RSI" value={minRsi} onChange={setMinRsi} />
          <NumberField label="Max RSI" value={maxRsi} onChange={setMaxRsi} />
          <NumberField label="Min vol ratio" value={minVolRatio} onChange={setMinVolRatio} step="0.1" />
          <div className="form-group">
            <div className="form-label">Sort by</div>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="change_1m_pct">1m %</option>
              <option value="change_1d_pct">1d %</option>
              <option value="rsi_14">RSI</option>
              <option value="vol_ratio_20">Vol ratio</option>
              <option value="last_close">Close</option>
            </select>
          </div>
          <div className="form-group">
            <div className="form-label">Limit</div>
            <input type="number" value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
          </div>
          <div className="spacer" />
          <CheckField label="Above SMA 20" checked={aboveSma20} onChange={setAboveSma20} />
          <CheckField label="Above SMA 200" checked={aboveSma200} onChange={setAboveSma200} />
          <CheckField label="MACD bullish" checked={macdBull} onChange={setMacdBull} />
        </div>

        <div className="row" style={{ marginTop: 14 }}>
          <button className="btn-primary" onClick={onScan} disabled={running}>
            {running ? "Scanning…" : "▶ Scan Market"}
          </button>
          {token && (
            <>
              <input placeholder="e.g. Momentum RSI>60" value={scanName} onChange={(e) => setScanName(e.target.value)} style={{ width: 200 }} />
              <button className="btn-secondary" onClick={onSaveScan} disabled={!scanName}>
                Save Scan
              </button>
            </>
          )}
        </div>
        {scanMsg && <p className="success-msg text-sm" style={{ marginTop: 8 }}>{scanMsg}</p>}

        {scans.length > 0 && (
          <div style={{ marginTop: 14 }}>
            <div className="form-label" style={{ marginBottom: 8 }}>Saved scans</div>
            <div className="chip-row">
              {scans.map((s) => (
                <span key={s.id} className="chip">
                  <button className="btn-xs" style={{ background: "none", color: "var(--text)", padding: 0 }} onClick={() => onRunSaved(s)}>
                    ▶ {s.name} ({s.market})
                  </button>
                  <button className="btn-xs" style={{ background: "none", color: "var(--down)", padding: 0 }} onClick={() => onDeleteScan(s)}>
                    ✕
                  </button>
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      {meta && <p className="text-muted text-sm" style={{ margin: "8px 4px" }}>{meta}</p>}
      {error && <p className="error-msg" style={{ margin: "8px 4px" }}>{error}</p>}

      {rows.length > 0 && (
        <section className="card">
          <div className="table-wrap tabular" style={{ maxHeight: 520 }}>
            <table>
              <thead>
                <tr>
                  <th>symbol</th><th className="num">close</th><th className="num">1d %</th><th className="num">5d %</th>
                  <th className="num">1m %</th><th className="num">3m %</th><th className="num">avg vol</th><th className="num">vol ratio</th>
                  <th className="num">RSI</th><th className="num">%B</th><th>SMA20</th><th>SMA50</th><th>SMA200</th><th>MACD</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.symbol}>
                    <td style={{ fontWeight: 600 }}>{r.symbol}</td>
                    <td className="num">{r.last_close.toFixed(2)}</td>
                    <td className={`num ${r.change_1d_pct != null && r.change_1d_pct >= 0 ? "text-up" : "text-down"}`}>{r.change_1d_pct?.toFixed(2) ?? "—"}</td>
                    <td className={`num ${r.change_5d_pct != null && r.change_5d_pct >= 0 ? "text-up" : "text-down"}`}>{r.change_5d_pct?.toFixed(2) ?? "—"}</td>
                    <td className={`num ${r.change_1m_pct != null && r.change_1m_pct >= 0 ? "text-up" : "text-down"}`}>{r.change_1m_pct?.toFixed(2) ?? "—"}</td>
                    <td className={`num ${r.change_3m_pct != null && r.change_3m_pct >= 0 ? "text-up" : "text-down"}`}>{r.change_3m_pct?.toFixed(2) ?? "—"}</td>
                    <td className="num">{r.avg_volume_20 != null ? Math.round(r.avg_volume_20).toLocaleString() : "—"}</td>
                    <td className="num">{r.vol_ratio_20 != null ? r.vol_ratio_20.toFixed(2) : "—"}</td>
                    <td className={`num ${r.rsi_14 != null && r.rsi_14 >= 70 ? "text-down" : r.rsi_14 != null && r.rsi_14 <= 30 ? "text-up" : ""}`}>{r.rsi_14?.toFixed(1) ?? "—"}</td>
                    <td className="num">{r.bb_position != null ? r.bb_position.toFixed(2) : "—"}</td>
                    <td>{r.above_sma_20 == null ? "—" : r.above_sma_20 ? "✅" : "❌"}</td>
                    <td>{r.above_sma_50 == null ? "—" : r.above_sma_50 ? "✅" : "❌"}</td>
                    <td>{r.above_sma_200 == null ? "—" : r.above_sma_200 ? "✅" : "❌"}</td>
                    <td>{r.macd_above_signal == null ? "—" : r.macd_above_signal ? "✅" : "❌"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}
