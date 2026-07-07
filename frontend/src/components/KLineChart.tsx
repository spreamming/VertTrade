import {
  CandlestickSeries,
  ColorType,
  createChart,
  CrosshairMode,
  HistogramSeries,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type ISeriesApi,
  type Time,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { KlineBar, MoneyflowBar } from "../types/stock";

type KLineChartProps = {
  bars: KlineBar[];
  moneyflowBars?: MoneyflowBar[];
};

function toChartTime(date: string): Time {
  if (date.includes(":")) {
    return Math.floor(new Date(date.replace(" ", "T")).getTime() / 1000) as Time;
  }
  return date as Time;
}

function formatChineseChartDate(time: Time): string {
  if (typeof time === "string") {
    const date = new Date(time.replace(" ", "T"));
    if (!Number.isNaN(date.getTime())) {
      const hasTime = time.includes(":");
      const dateText = `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
      return hasTime
        ? `${dateText} ${date.toLocaleTimeString("zh-CN", { hour12: false })}`
        : dateText;
    }
    return time;
  }

  if (typeof time === "number") {
    const date = new Date(time * 1000);
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
  }

  return `${time.year}年${time.month}月${time.day}日`;
}

function formatChineseTickDate(time: Time): string {
  if (typeof time === "string") {
    const date = new Date(time.replace(" ", "T"));
    if (!Number.isNaN(date.getTime())) {
      if (time.includes(":")) {
        return date.toLocaleTimeString("zh-CN", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        });
      }
      const currentYear = new Date().getFullYear();
      const suffix = `${date.getMonth() + 1}月${date.getDate()}日`;
      return date.getFullYear() === currentYear
        ? suffix
        : `${date.getFullYear()}年${suffix}`;
    }
  }

  return formatChineseChartDate(time);
}

export function KLineChart({ bars, moneyflowBars = [] }: KLineChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const moneyflowRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#111827" },
        textColor: "#cbd5e1",
      },
      grid: {
        vertLines: { color: "#1f2937" },
        horzLines: { color: "#1f2937" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      localization: {
        timeFormatter: formatChineseChartDate,
      },
      rightPriceScale: {
        borderColor: "#334155",
      },
      timeScale: {
        borderColor: "#334155",
        timeVisible: true,
        secondsVisible: false,
        tickMarkFormatter: formatChineseTickDate,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#ef4444",
      downColor: "#22c55e",
      borderUpColor: "#ef4444",
      borderDownColor: "#22c55e",
      wickUpColor: "#ef4444",
      wickDownColor: "#22c55e",
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    const moneyflowSeries = chart.addSeries(HistogramSeries, {
      priceFormat: {
        type: "custom",
        formatter: (value: number) => {
          const abs = Math.abs(value);
          if (abs >= 100_000_000) {
            return `${(value / 100_000_000).toFixed(1)}亿`;
          }
          if (abs >= 10_000) {
            return `${(value / 10_000).toFixed(0)}万`;
          }
          return value.toFixed(0);
        },
      },
      priceScaleId: "moneyflow",
    });

    chart.priceScale("right").applyOptions({
      scaleMargins: { top: 0.05, bottom: 0.42 },
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.64, bottom: 0.2 },
    });

    chart.priceScale("moneyflow").applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    });

    chartRef.current = chart;
    candleRef.current = candleSeries;
    volumeRef.current = volumeSeries;
    moneyflowRef.current = moneyflowSeries;

    return () => {
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      volumeRef.current = null;
      moneyflowRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (
      !candleRef.current ||
      !volumeRef.current ||
      !moneyflowRef.current ||
      bars.length === 0
    ) {
      return;
    }

    const candleData: CandlestickData<Time>[] = bars.map((bar) => ({
      time: toChartTime(bar.date),
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));

    const volumeData: HistogramData<Time>[] = bars.map((bar, index) => {
      const previousClose = index > 0 ? bars[index - 1].close : bar.open;
      const isUp = bar.close >= previousClose;
      return {
        time: toChartTime(bar.date),
        value: bar.volume,
        color: isUp ? "rgba(239, 68, 68, 0.5)" : "rgba(34, 197, 94, 0.5)",
      };
    });

    const moneyflowByDate = new Map(
      moneyflowBars.map((bar) => [bar.date, bar.main_net_inflow]),
    );
    const moneyflowData: HistogramData<Time>[] = [];
    for (const bar of bars) {
      const value = moneyflowByDate.get(bar.date);
      if (value !== undefined) {
        moneyflowData.push({
          time: toChartTime(bar.date),
          value,
          color:
            value >= 0
              ? "rgba(239, 68, 68, 0.75)"
              : "rgba(34, 197, 94, 0.75)",
        });
      }
    }

    candleRef.current.setData(candleData);
    volumeRef.current.setData(volumeData);
    moneyflowRef.current.setData(moneyflowData);
    chartRef.current?.timeScale().fitContent();
  }, [bars, moneyflowBars]);

  return <div ref={containerRef} className="kline-chart" />;
}
