import type { WatchlistItem } from "../api/client";
import { formatMoneyAmount } from "../utils/money";

type WatchlistReviewPanelProps = {
  items: WatchlistItem[];
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

function sortByNumber<T>(
  items: T[],
  getValue: (item: T) => number | null | undefined,
  direction: "asc" | "desc",
): T[] {
  return [...items]
    .filter((item) => getValue(item) !== null && getValue(item) !== undefined)
    .sort((a, b) => {
      const left = getValue(a) ?? 0;
      const right = getValue(b) ?? 0;
      return direction === "asc" ? left - right : right - left;
    });
}

export function WatchlistReviewPanel({ items }: WatchlistReviewPanelProps) {
  const highPosition = items.filter(
    (item) => item.position_score !== null && item.position_score !== undefined && item.position_score >= 80,
  );
  const lowPosition = items.filter(
    (item) => item.position_score !== null && item.position_score !== undefined && item.position_score <= 20,
  );
  const netInflow = items.filter(
    (item) => item.main_net_inflow !== null && item.main_net_inflow !== undefined && item.main_net_inflow > 0,
  );
  const netOutflow = items.filter(
    (item) => item.main_net_inflow !== null && item.main_net_inflow !== undefined && item.main_net_inflow < 0,
  );
  const strongest = sortByNumber(items, (item) => item.change_percent, "desc")[0];
  const weakest = sortByNumber(items, (item) => item.change_percent, "asc")[0];
  const topInflow = sortByNumber(items, (item) => item.main_net_inflow, "desc")[0];
  const topOutflow = sortByNumber(items, (item) => item.main_net_inflow, "asc")[0];

  if (items.length === 0) {
    return (
      <section className="status-card wide-card">
        <h2>自选股复盘摘要</h2>
        <p className="empty-text">添加自选股后，这里会汇总价格位置和资金流观察结果。</p>
      </section>
    );
  }

  return (
    <section className="status-card wide-card">
      <div className="section-header">
        <div>
          <h2>自选股复盘摘要</h2>
          <p className="section-copy">
            汇总自选股的价格位置、涨跌强弱和主力资金流，辅助每日复盘观察。
          </p>
        </div>
      </div>

      <div className="review-summary-grid">
        <div>
          <dt>高位观察</dt>
          <dd className="quote-up">{highPosition.length}</dd>
          <p>价格位置 ≥ 80 分</p>
        </div>
        <div>
          <dt>低位观察</dt>
          <dd className="quote-down">{lowPosition.length}</dd>
          <p>价格位置 ≤ 20 分</p>
        </div>
        <div>
          <dt>主力净流入</dt>
          <dd className="quote-up">{netInflow.length}</dd>
          <p>自选股资金流为正</p>
        </div>
        <div>
          <dt>主力净流出</dt>
          <dd className="quote-down">{netOutflow.length}</dd>
          <p>自选股资金流为负</p>
        </div>
      </div>

      <ul className="stage-list">
        <li>
          涨幅最强：{strongest ? `${strongest.name}（${formatNumber(strongest.change_percent)}%）` : "--"}
        </li>
        <li>
          跌幅较弱：{weakest ? `${weakest.name}（${formatNumber(weakest.change_percent)}%）` : "--"}
        </li>
        <li>
          主力净流入最多：{topInflow ? `${topInflow.name}（${formatMoneyAmount(topInflow.main_net_inflow)}）` : "--"}
        </li>
        <li>
          主力净流出最多：{topOutflow ? `${topOutflow.name}（${formatMoneyAmount(topOutflow.main_net_inflow)}）` : "--"}
        </li>
      </ul>

      <p className="position-note">
        该摘要只用于整理自选股观察重点，不构成买卖建议或交易信号。
      </p>
    </section>
  );
}
