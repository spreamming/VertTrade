import {
  ColorType,
  createChart,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  type HistogramData,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type Time,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { TimeSharePoint } from "../types/stock";

type TimeShareChartProps = {
  points: TimeSharePoint[];
};

function toChartTime(value: string): Time {
  return Math.floor(new Date(value.replace(" ", "T")).getTime() / 1000) as Time;
}

export function TimeShareChart({ points }: TimeShareChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const priceRef = useRef<ISeriesApi<"Line"> | null>(null);
  const averageRef = useRef<ISeriesApi<"Line"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);

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
      rightPriceScale: {
        borderColor: "#334155",
        scaleMargins: { top: 0.08, bottom: 0.28 },
      },
      timeScale: {
        borderColor: "#334155",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const priceSeries = chart.addSeries(LineSeries, {
      color: "#38bdf8",
      lineWidth: 2,
    });
    const averageSeries = chart.addSeries(LineSeries, {
      color: "#f59e0b",
      lineWidth: 1,
    });
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.78, bottom: 0 },
    });

    chartRef.current = chart;
    priceRef.current = priceSeries;
    averageRef.current = averageSeries;
    volumeRef.current = volumeSeries;

    return () => {
      chart.remove();
      chartRef.current = null;
      priceRef.current = null;
      averageRef.current = null;
      volumeRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!priceRef.current || !averageRef.current || !volumeRef.current) {
      return;
    }

    const priceData: LineData<Time>[] = points.map((point) => ({
      time: toChartTime(point.time),
      value: point.price,
    }));
    const averageData: LineData<Time>[] = points
      .filter((point) => point.average_price !== null && point.average_price !== undefined)
      .map((point) => ({
        time: toChartTime(point.time),
        value: point.average_price ?? point.price,
      }));
    const volumeData: HistogramData<Time>[] = points.map((point, index) => {
      const previous = index > 0 ? points[index - 1].price : point.price;
      return {
        time: toChartTime(point.time),
        value: point.volume ?? 0,
        color:
          point.price >= previous
            ? "rgba(239, 68, 68, 0.45)"
            : "rgba(34, 197, 94, 0.45)",
      };
    });

    priceRef.current.setData(priceData);
    averageRef.current.setData(averageData);
    volumeRef.current.setData(volumeData);
    chartRef.current?.timeScale().fitContent();
  }, [points]);

  return <div ref={containerRef} className="timeshare-chart" />;
}
