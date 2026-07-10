import type { MoneyflowBar, MoneyflowResponse } from "../types/stock";
import { formatMoneyAmount } from "../utils/money";
import {
  getMoneyflowViewOption,
  hasMoneyflowBreakdown,
  isMoneyflowViewAvailable,
  MONEYFLOW_VIEW_OPTIONS,
  moneyflowFlowLabel,
  resolveMoneyflowNet,
  resolveMoneyflowNetRatio,
  type MoneyflowView,
} from "../utils/moneyflow";

type MoneyFlowPanelProps = {
  moneyflow: MoneyflowResponse | null;
  loading?: boolean;
  error?: string | null;
  view: MoneyflowView;
  onViewChange: (view: MoneyflowView) => void;
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

function MoneyflowViewSwitcher({
  view,
  bars,
  onViewChange,
}: {
  view: MoneyflowView;
  bars: MoneyflowBar[];
  onViewChange: (view: MoneyflowView) => void;
}) {
  return (
    <div className="moneyflow-view-switcher" role="group" aria-label="主力资金视角">
      {MONEYFLOW_VIEW_OPTIONS.map((option) => {
        const disabled = !isMoneyflowViewAvailable(bars, option.value);
        return (
          <button
            key={option.value}
            type="button"
            className={option.value === view ? "period-active" : ""}
            disabled={disabled}
            title={disabled ? "当前数据源未提供该口径的分单明细" : option.description}
            onClick={() => onViewChange(option.value)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

export function MoneyFlowPanel({
  moneyflow,
  loading = false,
  error = null,
  view,
  onViewChange,
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

  const viewOption = getMoneyflowViewOption(view);
  const latest: MoneyflowBar = moneyflow.bars[moneyflow.bars.length - 1];
  const latestNet = resolveMoneyflowNet(latest, view);
  const latestRatio = resolveMoneyflowNetRatio(latest, view);
  const recent = moneyflow.bars.slice(-5);
  const cumulative5 = recent.reduce((sum, bar) => {
    const value = resolveMoneyflowNet(bar, view);
    return sum + (value ?? 0);
  }, 0);
  const hasBreakdown = hasMoneyflowBreakdown(moneyflow.bars);
  const viewAvailable = isMoneyflowViewAvailable(moneyflow.bars, view);

  return (
    <section className="moneyflow-panel">
      <div className="section-header">
        <div>
          <h2>主力资金流</h2>
          <p className="section-copy">
            数据来源：{moneyflow.source || "东方财富（AKShare）"}。{viewOption.description}
            不是交易所官方字段。
          </p>
        </div>
        {latestNet != null ? (
          <span className={`flow-badge ${flowClass(latestNet)}`}>
            {moneyflowFlowLabel(view, latestNet)}
          </span>
        ) : null}
      </div>

      <MoneyflowViewSwitcher view={view} bars={moneyflow.bars} onViewChange={onViewChange} />

      {!viewAvailable ? (
        <p className="position-note">
          当前视角需要分单明细，但数据源仅返回汇总主力净流入。请切换回「主力（超大+大）」视角。
        </p>
      ) : null}

      {!hasBreakdown && view === "main" ? (
        <p className="position-note">
          当前为汇总口径，未返回超大/大/中/小单拆分；其他视角暂不可用。
        </p>
      ) : null}

      <div className="moneyflow-grid">
        <div>
          <dt>最新{viewOption.shortLabel}净流入</dt>
          <dd className={flowClass(latestNet)}>{formatMoneyAmount(latestNet)}</dd>
        </div>
        <div>
          <dt>{view === "main" ? "主力净占比" : "净占比"}</dt>
          <dd className={flowClass(latestRatio)}>{formatPercent(latestRatio)}</dd>
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

      {hasBreakdown ? (
        <div className="moneyflow-breakdown">
          <p className="position-note">最新一日分单明细（元）</p>
          <div className="moneyflow-grid moneyflow-grid-compact">
            <div>
              <dt>超大单</dt>
              <dd className={flowClass(latest.super_large_net_inflow)}>
                {formatMoneyAmount(latest.super_large_net_inflow)}
              </dd>
            </div>
            <div>
              <dt>大单</dt>
              <dd className={flowClass(latest.large_net_inflow)}>
                {formatMoneyAmount(latest.large_net_inflow)}
              </dd>
            </div>
            <div>
              <dt>中单</dt>
              <dd className={flowClass(latest.medium_net_inflow)}>
                {formatMoneyAmount(latest.medium_net_inflow)}
              </dd>
            </div>
            <div>
              <dt>小单</dt>
              <dd className={flowClass(latest.small_net_inflow)}>
                {formatMoneyAmount(latest.small_net_inflow)}
              </dd>
            </div>
          </div>
        </div>
      ) : null}

      <p className="position-note">
        资金流为观察维度，不代表真实资金去向，也不构成交易建议。
      </p>
    </section>
  );
}
