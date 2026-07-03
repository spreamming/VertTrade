import type { StockPosition } from "../api/client";

type PositionCardProps = {
  position: StockPosition | null;
  loading?: boolean;
};

function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) {
    return "--";
  }
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function zoneClass(zone: string | undefined): string {
  if (zone === "deep_bottom" || zone === "bottom_watch") {
    return "position-low";
  }
  if (zone === "high_watch" || zone === "top_risk") {
    return "position-high";
  }
  return "position-neutral";
}

export function PositionCard({ position, loading = false }: PositionCardProps) {
  if (loading && !position) {
    return <p className="loading-text">正在计算价格位置...</p>;
  }

  if (!position) {
    return null;
  }

  const score = Math.max(0, Math.min(100, position.position_score));

  return (
    <section className="position-card">
      <div className="section-header">
        <div>
          <h2>价格位置</h2>
          <p className="section-copy">
            基于最近 {position.window} 个交易日高低点计算，反映当前价格所处区间。
          </p>
        </div>
        <span className={`position-badge ${zoneClass(position.zone)}`}>
          {position.label}
        </span>
      </div>

      <div className="position-meter" aria-label={`价格位置分数 ${score}`}>
        <span style={{ width: `${score}%` }} />
      </div>

      <div className="position-grid">
        <div>
          <dt>位置分数</dt>
          <dd>{formatNumber(score)} / 100</dd>
        </div>
        <div>
          <dt>区间低点</dt>
          <dd>{formatNumber(position.rolling_low)}</dd>
        </div>
        <div>
          <dt>区间高点</dt>
          <dd>{formatNumber(position.rolling_high)}</dd>
        </div>
        <div>
          <dt>样本数量</dt>
          <dd>{position.sample_size} 日</dd>
        </div>
      </div>

      <p className="position-note">
        该指标只表示历史区间中的相对位置，不是买入或卖出信号。
      </p>
    </section>
  );
}
