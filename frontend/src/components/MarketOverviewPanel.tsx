import type { MarketBreadthSummary, MarketIndexSummary, MarketOverviewResponse } from "../types/stock";

type MarketOverviewPanelProps = {
  overview: MarketOverviewResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
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

function formatAmount(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "--";
  }
  if (value >= 1_0000_0000) {
    return `${(value / 1_0000_0000).toFixed(2)} 亿`;
  }
  if (value >= 1_0000) {
    return `${(value / 1_0000).toFixed(2)} 万`;
  }
  return formatNumber(value, 0);
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "--";
  }
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function changeClass(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "";
  }
  return value >= 0 ? "quote-up" : "quote-down";
}

function IndexCard({ index }: { index: MarketIndexSummary }) {
  return (
    <article className="index-card">
      <div className="index-card-header">
        <h3>{index.name}</h3>
        <span className="index-code">{index.code}</span>
      </div>
      <p className={`index-price ${changeClass(index.change_percent)}`}>
        {formatNumber(index.latest_price)}
      </p>
      <p className={`index-change ${changeClass(index.change_percent)}`}>
        {formatNumber(index.change_amount)} ({formatNumber(index.change_percent)}%)
      </p>
      <p className="index-meta">成交额 {formatAmount(index.amount)}</p>
    </article>
  );
}

function BreadthGrid({ breadth }: { breadth: MarketBreadthSummary }) {
  return (
    <div className="breadth-grid">
      <div>
        <dt>上涨</dt>
        <dd className="quote-up">{breadth.rising_count ?? "--"}</dd>
      </div>
      <div>
        <dt>下跌</dt>
        <dd className="quote-down">{breadth.falling_count ?? "--"}</dd>
      </div>
      <div>
        <dt>平盘</dt>
        <dd>{breadth.flat_count ?? "--"}</dd>
      </div>
      <div>
        <dt>涨停</dt>
        <dd className="quote-up">{breadth.limit_up_count ?? "--"}</dd>
      </div>
      <div>
        <dt>跌停</dt>
        <dd className="quote-down">{breadth.limit_down_count ?? "--"}</dd>
      </div>
      <div>
        <dt>停牌</dt>
        <dd>{breadth.suspended_count ?? "--"}</dd>
      </div>
      <div>
        <dt>活跃度</dt>
        <dd>{breadth.activity_ratio !== null && breadth.activity_ratio !== undefined ? `${formatNumber(breadth.activity_ratio)}%` : "--"}</dd>
      </div>
      <div>
        <dt>统计时间</dt>
        <dd>{formatDateTime(breadth.as_of)}</dd>
      </div>
    </div>
  );
}

export function MarketOverviewPanel({
  overview,
  loading,
  error,
  onRefresh,
}: MarketOverviewPanelProps) {
  const displayError = error ?? overview?.error ?? null;

  return (
    <section className="status-card wide-card">
      <div className="section-header">
        <div>
          <h2>市场概览</h2>
          <p className="section-copy">
            主要指数与 A 股涨跌家数，用于快速判断大盘环境；仅作观察参考，不构成交易建议。
          </p>
        </div>
        <button type="button" className="refresh-button" onClick={onRefresh}>
          刷新
        </button>
      </div>

      {loading && !overview ? <p className="loading-text">正在加载市场概览...</p> : null}
      {displayError ? <p className="table-note">{displayError}</p> : null}

      {overview && overview.indices.length > 0 ? (
        <div className="index-grid">
          {overview.indices.map((index) => (
            <IndexCard key={index.code} index={index} />
          ))}
        </div>
      ) : null}

      {overview?.breadth ? <BreadthGrid breadth={overview.breadth} /> : null}

      {overview ? (
        <div className="chart-meta-grid">
          <span>
            状态：
            {overview.is_stale ? "缓存数据" : "近实时"}
          </span>
          <span>刷新时间：{formatDateTime(overview.cache_time)}</span>
          {overview.source ? <span>数据来源：{overview.source}</span> : null}
        </div>
      ) : null}

      {overview?.notes && overview.notes.length > 0 ? (
        <ul className="stage-list compact-notes">
          {overview.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
