import type { DailyReviewResponse, RankingGroup, RankingItem } from "../api/client";
import { formatMoneyAmount } from "../utils/money";

type RankingPanelProps = {
  review: DailyReviewResponse | null;
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

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "--";
  }
  return `${formatNumber(value)}%`;
}

function sourceLabel(source: string | null | undefined): string {
  if (source === "akshare_ths") {
    return "同花顺";
  }
  if (source === "akshare_em_direct") {
    return "东方财富直连";
  }
  if (source === "akshare_em") {
    return "东方财富";
  }
  return "数据源";
}

function metricText(item: RankingItem): string {
  if (item.main_net_inflow !== null && item.main_net_inflow !== undefined) {
    return formatMoneyAmount(item.main_net_inflow);
  }
  if (item.amount !== null && item.amount !== undefined) {
    return formatMoneyAmount(item.amount);
  }
  if (item.turnover_rate !== null && item.turnover_rate !== undefined) {
    return `换手 ${formatPercent(item.turnover_rate)}`;
  }
  return formatPercent(item.change_percent);
}

function RankingCard({ group }: { group: RankingGroup }) {
  return (
    <article className="ranking-card">
      <div className="ranking-card-header">
        <h3>{group.title}</h3>
        {group.source ? (
          <span className="source-chip">{sourceLabel(group.source)}</span>
        ) : null}
      </div>

      {group.error ? <p className="table-note">{group.error}</p> : null}

      {!group.error && group.items.length === 0 ? (
        <p className="empty-text">暂无排行数据。</p>
      ) : null}

      {group.items.length > 0 ? (
        <ol className="ranking-list">
          {group.items.slice(0, 5).map((item, index) => {
            const changeClass =
              item.change_percent !== null &&
              item.change_percent !== undefined &&
              item.change_percent >= 0
                ? "quote-up"
                : "quote-down";

            return (
              <li key={`${group.key}-${item.code ?? item.name}`}>
                <span className="rank-index">{index + 1}</span>
                <span>
                  <strong>{item.name}</strong>
                  {item.code ? (
                    <small>
                      {item.code}
                      {item.exchange ? ` · ${item.exchange}` : ""}
                    </small>
                  ) : null}
                  {item.leading_stock ? <small>领涨：{item.leading_stock}</small> : null}
                </span>
                <span className="rank-metric">
                  <strong>{metricText(item)}</strong>
                  <small className={changeClass}>{formatPercent(item.change_percent)}</small>
                </span>
              </li>
            );
          })}
        </ol>
      ) : null}
    </article>
  );
}

export function RankingPanel({
  review,
  loading,
  error,
  onRefresh,
}: RankingPanelProps) {
  return (
    <section className="status-card wide-card">
      <div className="section-header">
        <div>
          <h2>每日复盘与排行榜</h2>
          <p className="section-copy">
            展示个股涨跌、成交、换手、主力资金，以及板块强弱和板块资金流。
            单个数据源失败时只影响对应榜单。
          </p>
        </div>
        <button type="button" className="refresh-button" onClick={onRefresh}>
          刷新复盘
        </button>
      </div>

      {loading ? <p className="loading-text">正在加载排行榜...</p> : null}
      {error ? <p className="search-error">{error}</p> : null}

      {review ? (
        <>
          <div className="ranking-grid">
            {review.groups.map((group) => (
              <RankingCard key={group.key} group={group} />
            ))}
          </div>
          <ul className="stage-list">
            {review.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  );
}
