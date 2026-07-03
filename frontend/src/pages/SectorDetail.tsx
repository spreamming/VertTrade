import { useCallback, useEffect, useState } from "react";

import {
  getIndustrySector,
  type SectorDetailResponse,
  type SectorSummary,
  type StockSummary,
} from "../api/client";
import { formatMoneyAmount } from "../utils/money";

type SectorDetailProps = {
  sector: SectorSummary;
  onBack: () => void;
  onOpenStock: (stock: StockSummary) => void;
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

export function SectorDetail({ sector, onBack, onOpenStock }: SectorDetailProps) {
  const [detail, setDetail] = useState<SectorDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSector = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      setDetail(await getIndustrySector(sector));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "加载板块详情失败");
    } finally {
      setLoading(false);
    }
  }, [sector]);

  useEffect(() => {
    void loadSector();
  }, [loadSector]);

  const detailSourceText =
    detail?.source === "akshare_ths" ? "同花顺（AKShare）" : "东方财富（AKShare）";

  return (
    <main className="app-shell dashboard-shell">
      <header className="stock-header">
        <button type="button" className="back-button" onClick={onBack}>
          返回
        </button>
        <div>
          <p className="eyebrow">行业板块 · {sector.code}</p>
          <h1>{sector.name}</h1>
          <p className="section-copy">
            成分股来自 {detail ? detailSourceText : "AKShare"} 行业板块数据，
            用于观察板块内部强弱。
          </p>
        </div>
        <button
          type="button"
          className="refresh-button"
          onClick={() => void loadSector()}
          disabled={loading}
        >
          刷新
        </button>
      </header>

      {error ? <p className="search-error">{error}</p> : null}

      <section className="quote-grid">
        <div>
          <dt>板块涨跌幅</dt>
          <dd
            className={
              sector.change_percent !== null &&
              sector.change_percent !== undefined &&
              sector.change_percent >= 0
                ? "quote-up"
                : "quote-down"
            }
          >
            {formatPercent(sector.change_percent)}
          </dd>
        </div>
        <div>
          <dt>换手率</dt>
          <dd>{formatPercent(sector.turnover_rate)}</dd>
        </div>
        <div>
          <dt>上涨 / 下跌</dt>
          <dd>
            {sector.rising_count ?? "--"} / {sector.falling_count ?? "--"}
          </dd>
        </div>
        <div>
          <dt>总市值</dt>
          <dd>{formatMoneyAmount(sector.market_value)}</dd>
        </div>
      </section>

      <section className="status-card wide-card">
        <div className="section-header">
          <div>
            <h2>成分股</h2>
            <p className="section-copy">
              点击股票名称可进入个股详情页，继续查看 K 线、价格位置和资金流。
            </p>
          </div>
        </div>

        {loading ? <p className="loading-text">正在加载成分股...</p> : null}

        {detail && detail.constituents.length > 0 ? (
          <div className="watchlist-table-wrap">
            <table className="watchlist-table">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>代码</th>
                  <th>最新价</th>
                  <th>涨跌幅</th>
                  <th>成交额</th>
                  <th>换手率</th>
                  <th>估值</th>
                </tr>
              </thead>
              <tbody>
                {detail.constituents.map((item) => {
                  const changeClass =
                    item.change_percent !== null &&
                    item.change_percent !== undefined &&
                    item.change_percent >= 0
                      ? "quote-up"
                      : "quote-down";

                  return (
                    <tr key={item.code}>
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
                      </td>
                      <td>
                        {item.code} · {item.exchange}
                      </td>
                      <td>{formatNumber(item.latest_price)}</td>
                      <td className={changeClass}>{formatPercent(item.change_percent)}</td>
                      <td>{formatMoneyAmount(item.amount)}</td>
                      <td>{formatPercent(item.turnover_rate)}</td>
                      <td>
                        PE {formatNumber(item.pe_dynamic)}
                        <p className="table-note table-note-muted">
                          PB {formatNumber(item.pb)}
                        </p>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}

        {!loading && !error && detail && detail.constituents.length === 0 ? (
          <p className="empty-text">暂无成分股数据。</p>
        ) : null}
      </section>
    </main>
  );
}
