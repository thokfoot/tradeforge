"use client";

import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  LineStyle,
  createChart,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type Time,
} from "lightweight-charts";
import { getOhlcv, type Bar, type Market, type Position } from "@/lib/api";

const UP = "#14e8b0";
const DOWN = "#ff4d7a";
const SL_COLOR = "#ff4d7a";
const TP_COLOR = "#14e8b0";
const ENTRY_COLOR = "#38bdf8";

function toChartTime(date: string): Time {
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(date)) {
    return Math.floor(new Date(date.replace(" ", "T")).getTime() / 1000) as Time;
  }
  return date as Time;
}

export default function PaperChart({
  market,
  symbol,
  position,
  onLevelsChanged,
  onClose,
  onReverse,
}: {
  market: Market;
  symbol: string;
  position: Position | null;
  onLevelsChanged: (sl: number | null, tp: number | null) => void;
  onClose: () => void;
  onReverse: () => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const linesRef = useRef<{ entry?: IPriceLine; sl?: IPriceLine; tp?: IPriceLine }>({});
  const posRef = useRef<Position | null>(null);
  const draggingRef = useRef<"sl" | "tp" | null>(null);
  const [bars, setBars] = useState<Bar[]>([]);
  const [height, setHeight] = useState(420);
  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null);
  const [error, setError] = useState("");

  posRef.current = position;

  useEffect(() => {
    const syncHeight = () => {
      setHeight(window.innerWidth <= 640 ? 300 : window.innerWidth <= 960 ? 360 : 420);
    };
    syncHeight();
    window.addEventListener("resize", syncHeight);
    return () => window.removeEventListener("resize", syncHeight);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setError("");
    getOhlcv(market, symbol, "1d")
      .then((res) => {
        if (!cancelled) setBars(res.bars);
      })
      .catch((e) => {
        if (!cancelled) setError(String(e.message ?? e));
      });
    return () => {
      cancelled = true;
    };
  }, [market, symbol]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const chart = createChart(el, {
      width: el.clientWidth,
      height,
      layout: { background: { color: "transparent" }, textColor: "#94a3b8" },
      grid: {
        vertLines: { color: "rgba(26,37,64,0.45)" },
        horzLines: { color: "rgba(26,37,64,0.45)" },
      },
      rightPriceScale: { borderColor: "#1a2540" },
      timeScale: { borderColor: "#1a2540", timeVisible: true },
      crosshair: { mode: 0 },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: UP,
      downColor: DOWN,
      borderVisible: false,
      wickUpColor: UP,
      wickDownColor: DOWN,
    });
    series.setData(
      bars.map((b) => ({
        time: toChartTime(b.date),
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      }))
    );
    chart.timeScale().fitContent();
    chartRef.current = chart;
    seriesRef.current = series;
    const onResize = () => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth, height });
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      linesRef.current = {};
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [bars, height]);

  useEffect(() => {
    const series = seriesRef.current;
    if (!series || !chartRef.current) return;
    const lines = linesRef.current;
    const sync = (
      key: "sl" | "tp" | "entry",
      price: number | null,
      color: string,
      style: LineStyle,
      title: string
    ) => {
      const existing = lines[key];
      if (price == null) {
        if (existing) {
          series.removePriceLine(existing);
          delete lines[key];
        }
        return;
      }
      if (existing) {
        existing.applyOptions({ price, color, lineStyle: style, title });
      } else {
        lines[key] = series.createPriceLine({
          price,
          color,
          lineWidth: 1,
          lineStyle: style,
          axisLabelVisible: true,
          title,
        });
      }
    };
    const p = position;
    if (p) {
      sync("entry", p.avg_price, ENTRY_COLOR, LineStyle.Solid, "Entry");
      sync("sl", p.sl, SL_COLOR, LineStyle.Dashed, "SL");
      sync("tp", p.tp, TP_COLOR, LineStyle.Dashed, "TP");
    } else {
      sync("entry", null, ENTRY_COLOR, LineStyle.Solid, "Entry");
      sync("sl", null, SL_COLOR, LineStyle.Dashed, "SL");
      sync("tp", null, TP_COLOR, LineStyle.Dashed, "TP");
    }
  }, [position, bars]);

  useEffect(() => {
    if (!menu) return;
    const close = () => setMenu(null);
    window.addEventListener("click", close);
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
    });
    return () => {
      window.removeEventListener("click", close);
    };
  }, [menu]);

  function lineY(price: number | null | undefined): number | null {
    if (price == null || !seriesRef.current) return null;
    return seriesRef.current.priceToCoordinate(price);
  }

  function onPointerDown(e: React.PointerEvent<HTMLDivElement>) {
    if (menu || (e.target as HTMLElement).closest("[data-chart-action]")) return;
    const y = e.clientY - (containerRef.current?.getBoundingClientRect().top ?? 0);
    const slY = lineY(posRef.current?.sl ?? null);
    const tpY = lineY(posRef.current?.tp ?? null);
    if (slY != null && Math.abs(y - slY) <= 10) {
      draggingRef.current = "sl";
      containerRef.current?.setPointerCapture(e.pointerId);
    } else if (tpY != null && Math.abs(y - tpY) <= 10) {
      draggingRef.current = "tp";
      containerRef.current?.setPointerCapture(e.pointerId);
    }
  }

  function onPointerMove(e: React.PointerEvent<HTMLDivElement>) {
    const kind = draggingRef.current;
    if (!kind || !seriesRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const price = seriesRef.current.coordinateToPrice(y);
    if (price == null) return;
    const line = linesRef.current[kind];
    if (line) line.applyOptions({ price });
  }

  function onPointerUp() {
    const kind = draggingRef.current;
    draggingRef.current = null;
    if (!kind) return;
    const lines = linesRef.current;
    const sl = lines.sl?.options().price ?? null;
    const tp = lines.tp?.options().price ?? null;
    onLevelsChanged(sl, tp);
  }

  function onContextMenu(e: React.MouseEvent<HTMLDivElement>) {
    e.preventDefault();
    if (!posRef.current) return;
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    setMenu({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  }

  return (
    <div className="chart-box" style={{ minHeight: height }}>
      {error && <p className="error">{error}</p>}
      <div
        ref={containerRef}
        style={{ height: bars.length ? height : 0 }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onContextMenu={onContextMenu}
      >
        {bars.length === 0 && !error && (
          <div className="empty-state">
            <div className="empty-icon">📈</div>
            <div className="empty-title">Loading</div>
            Fetching {symbol} ...
          </div>
        )}
      </div>
      {menu && (
        <div
          className="chart-menu"
          data-chart-action="menu"
          style={{ left: menu.x, top: menu.y }}
          onClick={(e) => e.stopPropagation()}
        >
          <button data-chart-action onClick={() => { setMenu(null); onClose(); }}>
            Close Position
          </button>
          <button data-chart-action onClick={() => { setMenu(null); onReverse(); }}>
            Reverse Position
          </button>
        </div>
      )}
    </div>
  );
}
