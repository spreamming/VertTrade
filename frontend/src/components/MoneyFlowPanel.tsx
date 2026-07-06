import type { MoneyflowBar, MoneyflowResponse } from "../types/stock";
import { formatMoneyAmount } from "../utils/money";

type MoneyFlowPanelProps = {
  moneyflow: MoneyflowResponse | null;
  loading?: boolean;
  error?: string | null;
};

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "--";
  }
  return `${value.toFixed(2)}%`;
}

function flowClass(value: number | null | undefined): string {
  if (value === null || value === undefined || value === 0) {
    return "flow-neutral";
  }
  return value > 0 ? "quote-up" : "quote-down";
}

export function MoneyFlowPanel({
  moneyflow,
  loading = false,
  error = null,
}: MoneyFlowPanelProps) {
  if (loading && !moneyflow) {
    return <p className="loading-text">正在加载主力资金流...</p>;
  }

  if (error && !moneyflow) {
    return (
      <section className="moneyflow-panel">
        <div className="section-header">
          <div>
            <h2>主力资金流</h2>
            <p className="section-copy">
              数据来源：东方财富（AKShare）。当前资金流数据暂不可用，K 线和价格位置仍可正常查看。
            </p>
          </div>
        </div>
        <p className="search-error">{error}</p>
      </section>
    );
  }

  if (!moneyflow || moneyflow.bars.length === 0) {
    return (
      <section className="moneyflow-panel">
        <div className="section-header">
          <div>
            <h2>主力资金流</h2>
            <p className="section-copy">
              暂无该股票的主力资金流数据。K 线、价格位置和近实时行情仍可正常查看。
            </p>
          </div>
        </div>
      </section>
    );
  }

  const latest: MoneyflowBar = moneyflow.bars[moneyflow.bars.length - 1];
  const recent = moneyflow.bars.slice(-5);
  const cumulative5 = recent.reduce((sum, bar) => sum + bar.main_net_inflow, 0);

  return (
    <section className="moneyflow-panel">
      <div className="section-header">
        <div>
          <h2>主力资金流</h2>
          <p className="section-copy">
            数据来源：东方财富（AKShare），反映数据商口径下的主力净流入，不是交易所官方字段。
          </p>
        </div>
        <span className={`flow-badge ${flowClass(latest.main_net_inflow)}`}>
          {latest.main_net_inflow >= 0 ? "主力净流入" : "主力净流出"}
        </span>
      </div>

      <div className="moneyflow-grid">
        <div>
          <dt>最新主力净流入</dt>
          <dd className={flowClass(latest.main_net_inflow)}>
            {formatMoneyAmount(latest.main_net_inflow)}
          </dd>
        </div>
        <div>
          <dt>主力净占比</dt>
          <dd className={flowClass(latest.main_net_ratio)}>
            {formatPercent(latest.main_net_ratio)}
          </dd>
        </div>
        <div>
          <dt>近 5 日累计</dt>
          <dd className={flowClass(cumulative5)}>{formatMoneyAmount(cumulative5)}</dd>
        </div>
        <div>
          <dt>数据日期</dt>
          <dd>{latest.date}</dd>
        </div>
      </div>

      <p className="position-note">
        资金流为观察维度，不代表真实资金去向，也不构成交易建议。
      </p>
    </section>
  );
}
