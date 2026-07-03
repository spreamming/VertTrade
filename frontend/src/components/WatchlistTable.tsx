import type { StockSummary, WatchlistItem } from "../api/client";

type WatchlistTableProps = {
  items: WatchlistItem[];
  loading: boolean;
  onOpenStock: (stock: StockSummary) => void;
  onDelete: (id: number) => void;
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

export function WatchlistTable({
  items,
  loading,
  onOpenStock,
  onDelete,
}: WatchlistTableProps) {
  if (loading && items.length === 0) {
    return <p className="loading-text">正在加载自选股...</p>;
  }

  if (items.length === 0) {
    return <p className="empty-text">暂无自选股。请先搜索股票并添加到自选。</p>;
  }

  return (
    <div className="watchlist-table-wrap">
      <table className="watchlist-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>代码</th>
            <th>最新价</th>
            <th>涨跌幅</th>
            <th>价格位置</th>
            <th>交易日期</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const changeClass =
              item.change_percent !== null &&
              item.change_percent !== undefined &&
              item.change_percent >= 0
                ? "quote-up"
                : "quote-down";

            return (
              <tr key={item.id}>
                <td>
                  <button
                    type="button"
                    className="table-link"
                    onClick={() =>
                      onOpenStock({
                        code: item.code,
                        name: item.name,
                        exchange: item.exchange,
                      })
                    }
                  >
                    {item.name}
                  </button>
                  {item.quote_error ? (
                    <p className="table-note">{item.quote_error}</p>
                  ) : null}
                </td>
                <td>
                  {item.code} · {item.exchange}
                </td>
                <td>{formatNumber(item.latest_price)}</td>
                <td className={changeClass}>{formatPercent(item.change_percent)}</td>
                <td>
                  {item.position_score !== null &&
                  item.position_score !== undefined &&
                  item.position_label ? (
                    <span className="position-chip">
                      {item.position_label} · {formatNumber(item.position_score)}分
                    </span>
                  ) : (
                    "--"
                  )}
                  {item.position_error ? (
                    <p className="table-note">{item.position_error}</p>
                  ) : null}
                </td>
                <td>{item.trade_date ?? "--"}</td>
                <td>
                  <button
                    type="button"
                    className="danger-button"
                    onClick={() => onDelete(item.id)}
                  >
                    删除
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
