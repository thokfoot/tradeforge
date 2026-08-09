"use client";

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";

export default function Admin() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/health`).then(r => r.json()).then(setStatus).catch(e => setErr(String(e)));
  }, []);

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">System Status</div>
          <div className="card-subtitle">Server health &amp; configuration</div>
        </div>
      </div>
      {err && <div className="error-msg">{err}</div>}
      {status && (
        <div className="metrics-grid">
          {Object.entries(status).map(([k, v]) => (
            <div key={k} className="metric-card">
              <div className="metric-label">{k}</div>
              <div className="metric-value">{String(v)}</div>
            </div>
          ))}
        </div>
      )}
      <div className="metrics-grid" style={{ marginTop: 16 }}>
        {["Backend: Live", "DB: JSON", "Data: Parquet", "AI: Gemini Flash", "Markets: IN+US+CRYPTO", "Tauri: 21.8 MB .exe"].map(s => {
          const [l, v] = s.split(": ");
          return <div key={l} className="metric-card"><div className="metric-label">{l}</div><div className="metric-value text-sm">{v}</div></div>;
        })}
      </div>
    </div>
  );
}
