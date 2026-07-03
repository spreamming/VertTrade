import type { SectorSummary } from "../api/client";
import { formatMoneyAmount } from "../utils/money";

type SectorPanelProps = {
  sectors: SectorSummary[];
  loading: boolean;
  error: string | null;
  source: string | null;
  onRefresh: () => void;
  onOpenSector: (sector: SectorSummary) => void;
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

export function SectorPanel({
  sectors,
  loading,
  error,
  source,
  onRefresh,
  onOpenSector,
}: SectorPanelProps) {
  const sourceText =
    source === "akshare_ths" ? "同花顺（AKShare）" : "东方财富（AKShare）";

  return (
    <section className="status-card wide-card">
      <div className="section-header">
        <div>
          <h2>行业板块</h2>
          <p className="section-copy">
            查看行业板块涨跌、涨跌家数和领涨股票。点击板块名称可查看成分股。
            {source ? ` 当前数据来源：${sourceText}。` : ""}
          </p>
        </div>
        <button type="button" className="refresh-button" onClick={onRefresh}>
          刷新板块
        </button>
      </div>

      {loading ? <p className="loading-text">正在加载行业板块...</p> : null}
      {error ? <p className="search-error">{error}</p> : null}

      {!loading && !error && sectors.length === 0 ? (
        <p className="empty-text">暂无行业板块数据。</p>
      ) : null}

      {sectors.length > 0 ? (
        <div className="watchlist-table-wrap">
          <table className="watchlist-table">
            <thead>
              <tr>
                <th>板块</th>
                <th>涨跌幅</th>
                <th>成交额 / 总市值</th>
                <th>涨跌家数</th>
                <th>资金流</th>
                <th>领涨股票</th>
              </tr>
            </thead>
            <tbody>
              {sectors.slice(0, 20).map((sector) => {
                const changeClass =
                  sector.change_percent !== null &&
                  sector.change_percent !== undefined &&
                  sector.change_percent >= 0
                    ? "quote-up"
                    : "quote-down";

                return (
                  <tr key={sector.code}>
                    <td>
                      <button
                        type="button"
                        className="table-link"
                        onClick={() => onOpenSector(sector)}
                      >
                        {sector.name}
                      </button>
                      <p className="table-note table-note-muted">{sector.code}</p>
                    </td>
                    <td className={changeClass}>{formatPercent(sector.change_percent)}</td>
                    <td>
                      {formatMoneyAmount(sector.amount ?? sector.market_value)}
                      <p className="table-note table-note-muted">
                        {sector.amount !== null && sector.amount !== undefined
                          ? "成交额"
                          : "总市值"}
                        {sector.turnover_rate !== null &&
                        sector.turnover_rate !== undefined
                          ? ` · 换手 ${formatPercent(sector.turnover_rate)}`
                          : ""}
                      </p>
                    </td>
                    <td>
                      {sector.rising_count ?? "--"} 涨 / {sector.falling_count ?? "--"} 跌
                    </td>
                    <td
                      className={
                        sector.main_net_inflow !== null &&
                        sector.main_net_inflow !== undefined &&
                        sector.main_net_inflow >= 0
                          ? "quote-up"
                          : sector.main_net_inflow !== null &&
                              sector.main_net_inflow !== undefined
                            ? "quote-down"
                            : undefined
                      }
                    >
                      {formatMoneyAmount(sector.main_net_inflow)}
                    </td>
                    <td>
                      {sector.leading_stock ?? "--"}
                      {sector.leading_stock_change_percent !== null &&
                      sector.leading_stock_change_percent !== undefined ? (
                        <p className="table-note table-note-muted">
                          {formatPercent(sector.leading_stock_change_percent)}
                        </p>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
