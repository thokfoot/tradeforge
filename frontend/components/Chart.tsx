"use client";

import { useEffect, useRef, useState } from "react";
import type { CanvasRenderingTarget2D } from "fancy-canvas";
import {
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  LineStyle,
  createChart,
  createSeriesMarkers,
  customSeriesDefaultOptions,
  type CustomData,
  type CustomSeriesOptions,
  type CustomSeriesWhitespaceData,
  type ICustomSeriesPaneRenderer,
  type ICustomSeriesPaneView,
  type IChartApi,
  type PaneRendererCustomData,
  type PriceToCoordinateConverter,
  type SeriesPartialOptions,
  type Time,
} from "lightweight-charts";
import type { Bar } from "@/lib/api";

const UP = "#14e8b0";
const DOWN = "#ff4d7a";

export interface TradeMarker {
  timestamp: string;
  side: string;
  price: number;
}

export interface TradeZone {
  entryTime: string;
  exitTime: string;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
}

interface ZoneDatum extends CustomData {
  zoneId?: number;
  role?: "entry" | "exit";
  entryPrice?: number;
  exitPrice?: number;
  pnl?: number;
}

function toChartTime(date: string): Time {
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(date)) {
    return Math.floor(new Date(date.replace(" ", "T")).getTime() / 1000) as Time;
  }
  return date as Time;
}

function nearestBarTime(iso: string, bars: Bar[]): string | null {
  const target = new Date(iso.replace("T", " ")).getTime();
  if (Number.isNaN(target)) return null;
  let best: string | null = null;
  for (const b of bars) {
    const t = new Date(b.date.replace("T", " ")).getTime();
    if (t <= target) best = b.date;
    else break;
  }
  return best;
}

class TradeZoneRenderer implements ICustomSeriesPaneRenderer {
  _data: PaneRendererCustomData<Time, ZoneDatum> | null = null;

  update(data: PaneRendererCustomData<Time, ZoneDatum>) {
    this._data = data;
  }

  draw(
    target: CanvasRenderingTarget2D,
    priceConverter: PriceToCoordinateConverter
  ) {
    const data = this._data;
    if (!data) return;
    const zones = new Map<
      number,
      { x0: number; x1: number; y0: number; y1: number; pnl: number }
    >();
    for (const bar of data.bars) {
      const d = bar.originalData;
      if (d.zoneId == null || d.role == null) continue;
      const price = d.role === "entry" ? d.entryPrice : d.exitPrice;
      if (price == null) continue;
      const y = priceConverter(price);
      if (y == null) continue;
      const z = zones.get(d.zoneId) ?? { x0: 0, x1: 0, y0: 0, y1: 0, pnl: d.pnl ?? 0 };
      if (d.role === "entry") {
        z.x0 = bar.x;
        z.y0 = y;
      } else {
        z.x1 = bar.x;
        z.y1 = y;
      }
      zones.set(d.zoneId, z);
    }
    target.useMediaCoordinateSpace((scope) => {
      const ctx = scope.context;
      for (const z of zones.values()) {
        const x0 = Math.min(z.x0, z.x1);
        const x1 = Math.max(z.x0, z.x1);
        const y0 = Math.min(z.y0, z.y1);
        const y1 = Math.max(z.y0, z.y1);
        if (x1 - x0 < 1) continue;
        ctx.fillStyle = z.pnl >= 0 ? "rgba(20,232,176,0.13)" : "rgba(255,77,122,0.13)";
        ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
        ctx.strokeStyle = z.pnl >= 0 ? "rgba(20,232,176,0.42)" : "rgba(255,77,122,0.42)";
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
        ctx.setLineDash([]);
      }
    });
  }
}

const zoneRenderer = new TradeZoneRenderer();

const tradeZoneView: ICustomSeriesPaneView<Time, ZoneDatum> = {
  renderer() {
    return zoneRenderer;
  },
  defaultOptions() {
    return { ...customSeriesDefaultOptions };
  },
  update(data: PaneRendererCustomData<Time, ZoneDatum>) {
    zoneRenderer.update(data);
  },
  priceValueBuilder(plotRow: ZoneDatum) {
    const p = plotRow.role === "entry" ? plotRow.entryPrice : plotRow.exitPrice;
    return [p ?? 0];
  },
  isWhitespace(data: ZoneDatum | CustomSeriesWhitespaceData<Time>): data is CustomSeriesWhitespaceData<Time> {
    return (data as ZoneDatum).zoneId == null;
  },
};

const zoneOptions: SeriesPartialOptions<CustomSeriesOptions> = {
  lastValueVisible: false,
  priceLineVisible: false,
};

export default function Chart({ bars, type = "candles", showVolume = true, tradeMarkers = [], tradeZones = [], focusTime = null, height: propHeight }: {
  bars: Bar[];
  type?: "candles" | "line";
  showVolume?: boolean;
  tradeMarkers?: TradeMarker[];
  tradeZones?: TradeZone[];
  focusTime?: string | null;
  height?: number;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [height, setHeight] = useState(propHeight ?? 420);

  useEffect(() => {
    if (propHeight !== undefined) return;
    const syncHeight = () => {
      setHeight(window.innerWidth <= 640 ? 300 : window.innerWidth <= 960 ? 360 : 420);
    };
    syncHeight();
    window.addEventListener("resize", syncHeight);
    return () => window.removeEventListener("resize", syncHeight);
  }, [propHeight]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const chart = createChart(el, {
      width: el.clientWidth,
      height,
      layout: { background: { color: "transparent" }, textColor: "#94a3b8", fontSize: 12, fontFamily: "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" },
      grid: {
        vertLines: { color: "rgba(26,37,64,0.45)" },
        horzLines: { color: "rgba(26,37,64,0.45)" },
      },
      rightPriceScale: { borderColor: "#1a2540" },
      timeScale: { borderColor: "#1a2540", timeVisible: true },
      crosshair: { mode: 0 },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: UP,
      downColor: DOWN,
      borderVisible: false,
      wickUpColor: UP,
      wickDownColor: DOWN,
      priceLineColor: UP,
    });
    const lineSeries = chart.addSeries(LineSeries, {
      color: UP,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
      lastValueVisible: false,
      priceLineVisible: false,
      visible: showVolume,
    });
    chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    volumeSeries.createPriceLine({
      price: 0,
      color: "rgba(148,163,184,0.28)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: false,
    });

    const zoneSeries = chart.addCustomSeries(tradeZoneView, zoneOptions);

    if (type === "candles") {
      candleSeries.applyOptions({ visible: true });
      lineSeries.applyOptions({ visible: false });
      candleSeries.setData(
        bars.map((b) => ({
          time: toChartTime(b.date),
          open: b.open,
          high: b.high,
          low: b.low,
          close: b.close,
        }))
      );
    } else {
      candleSeries.applyOptions({ visible: false });
      lineSeries.applyOptions({ visible: true });
      lineSeries.setData(
        bars.map((b) => ({ time: toChartTime(b.date), value: b.close }))
      );
    }

    volumeSeries.setData(
      bars.map((b) => ({
        time: toChartTime(b.date),
        value: b.volume,
        color: b.close >= b.open ? "rgba(20,232,176,0.55)" : "rgba(255,77,122,0.55)",
      }))
    );

    const zoneData: ZoneDatum[] = [];
    tradeZones.forEach((z, i) => {
      const e = nearestBarTime(z.entryTime, bars);
      const x = nearestBarTime(z.exitTime, bars);
      if (!e || !x) return;
      zoneData.push({
        time: e as Time,
        zoneId: i,
        role: "entry",
        entryPrice: z.entryPrice,
        exitPrice: z.exitPrice,
        pnl: z.pnl,
      });
      zoneData.push({
        time: x as Time,
        zoneId: i,
        role: "exit",
        entryPrice: z.entryPrice,
        exitPrice: z.exitPrice,
        pnl: z.pnl,
      });
    });
    zoneSeries.applyOptions({ visible: zoneData.length > 0 });
    zoneSeries.setData(zoneData);

    chart.timeScale().fitContent();
    const vis = chart.timeScale().getVisibleLogicalRange();
    if (vis) chart.timeScale().setVisibleLogicalRange({ from: vis.from - 2, to: vis.to });

    if (type === "candles") {
      const timeToIndex = new Map<Time, number>(bars.map((b, i) => [toChartTime(b.date), i]));
      const log = chart.timeScale().getVisibleLogicalRange();
      const fromIdx = log ? Math.max(0, Math.floor(log.from)) : 0;
      const toIdx = log ? Math.ceil(log.to) : bars.length - 1;
      const markers = tradeMarkers
        .map((trade) => ({
          time: toChartTime(nearestBarTime(trade.timestamp, bars) ?? trade.timestamp) as Time,
          side: trade.side,
          price: trade.price,
        }))
        .filter((mk) => {
          const idx = timeToIndex.get(mk.time);
          return idx !== undefined && idx >= fromIdx && idx <= toIdx;
        })
        .map((mk) => ({
          time: mk.time,
          position: mk.side === "BUY" ? ("belowBar" as const) : ("aboveBar" as const),
          shape: mk.side === "BUY" ? ("arrowUp" as const) : ("arrowDown" as const),
          color: mk.side === "BUY" ? UP : DOWN,
          text: `${mk.side === "BUY" ? "B" : "S"} ${mk.price.toFixed(2)}`,
          size: 1 as const,
        }));
      if (markers.length > 0) {
        createSeriesMarkers(candleSeries, markers);
      }
    }

    chartRef.current = chart;
    const onResize = () => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth, height });
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [bars, height, type, showVolume, tradeMarkers, tradeZones]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart || !focusTime) return;
    const target = new Date(focusTime.replace("T", " ")).getTime();
    if (Number.isNaN(target)) return;
    let idx = -1;
    for (let i = 0; i < bars.length; i++) {
      const t = new Date(bars[i].date.replace("T", " ")).getTime();
      if (t <= target) idx = i;
      else break;
    }
    if (idx >= 0) {
      chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, idx - 15), to: idx + 15 });
    }
  }, [focusTime, bars]);

  return (
    <div className="chart-box" style={{ minHeight: height }}>
      {bars.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📈</div>
          <div className="empty-title">No data</div>
          Select a symbol or try another interval
        </div>
      )}
      <div ref={containerRef} style={{ height: bars.length ? height : 0 }} />
    </div>
  );
}
