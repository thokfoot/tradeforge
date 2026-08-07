"use client";

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  createChart,
  type IChartApi,
  type Time,
} from "lightweight-charts";
import type { Bar } from "@/lib/api";

export default function Chart({ bars }: { bars: Bar[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 400,
      layout: { background: { color: "#0a0f1e" }, textColor: "#9aa4bf" },
      grid: {
        vertLines: { color: "#141a2e" },
        horzLines: { color: "#141a2e" },
      },
      rightPriceScale: { borderColor: "#1e2740" },
      timeScale: { borderColor: "#1e2740", timeVisible: true },
      crosshair: { mode: 0 },
    });
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: false,
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });
    candleSeries.setData(
      bars.map((b) => ({
        time: b.date as Time,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      }))
    );
    chartRef.current = chart;
    const onResize = () => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth });
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [bars]);

  return <div ref={containerRef} className="chart-box" />;
}
