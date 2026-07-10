import type { KlineBar } from "../types/stock";

export type PositionPoint = {
  date: string;
  score: number;
};

export type PositionZoneLines = {
  rollingLow: number;
  rollingHigh: number;
  bottomZoneTop: number;
  topZoneBottom: number;
};

export function computePositionSeries(
  bars: KlineBar[],
  window: number,
): PositionPoint[] {
  if (bars.length === 0) {
    return [];
  }

  const points: PositionPoint[] = [];
  for (let index = window - 1; index < bars.length; index += 1) {
    const sample = bars.slice(index - window + 1, index + 1);
    const rollingLow = Math.min(...sample.map((bar) => bar.low));
    const rollingHigh = Math.max(...sample.map((bar) => bar.high));
    const latest = sample[sample.length - 1];
    const score =
      rollingHigh === rollingLow
        ? 50
        : ((latest.close - rollingLow) / (rollingHigh - rollingLow)) * 100;

    points.push({
      date: latest.date,
      score: Math.max(0, Math.min(100, Number(score.toFixed(2)))),
    });
  }

  return points;
}

export function buildPositionZoneLines(position: {
  rolling_low: number;
  rolling_high: number;
}): PositionZoneLines {
  const span = position.rolling_high - position.rolling_low;
  return {
    rollingLow: position.rolling_low,
    rollingHigh: position.rolling_high,
    bottomZoneTop: position.rolling_low + span * 0.2,
    topZoneBottom: position.rolling_low + span * 0.8,
  };
}
