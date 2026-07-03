import { useCallback, useEffect, useState } from "react";

import {
  addWatchlistItem,
  deleteWatchlistItem,
  getDashboard,
  type DashboardResponse,
  type StockSummary,
} from "../api/client";
import { SearchBox } from "../components/SearchBox";
import { WatchlistTable } from "../components/WatchlistTable";

type DashboardProps = {
  onOpenStock: (stock: StockSummary) => void;
};

export function Dashboard({ onOpenStock }: DashboardProps) {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      setDashboard(await getDashboard());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "加载首页数据失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  async function handleAddWatchlist(stock: StockSummary) {
    setActionMessage(null);
    setError(null);

    try {
      await addWatchlistItem(stock.code);
      setActionMessage(`${stock.name} 已加入自选股`);
      await loadDashboard();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "添加自选股失败");
    }
  }

  async function handleDeleteWatchlist(id: number) {
    setActionMessage(null);
    setError(null);

    try {
      await deleteWatchlistItem(id);
      setActionMessage("已从自选股删除");
      await loadDashboard();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "删除自选股失败");
    }
  }

  return (
    <main className="app-shell dashboard-shell">
      <section className="hero">
        <p className="eyebrow">个人 A 股看盘工具</p>
        <h1>VertTrade</h1>
        <p>
          首页用于维护自选股，并快速查看自选股的最新行情摘要。
          后续会继续加入主要指数、市场概览和板块资金流。
        </p>
      </section>

      <section className="dashboard-grid">
        <div className="status-card">
          <h2>添加自选股</h2>
          <p className="section-copy">
            搜索股票后点击结果，即可加入自选股。点击表格里的股票名称可进入个股详情页。
          </p>
          <SearchBox onSelect={handleAddWatchlist} />
          {actionMessage ? <p className="success-text">{actionMessage}</p> : null}
          {error ? <p className="search-error">{error}</p> : null}
        </div>

        <div className="status-card stat-card">
          <h2>自选股数量</h2>
          <p className="big-number">{dashboard?.watchlist_count ?? 0}</p>
          <p className="section-copy">当前本地自选股数量。</p>
        </div>
      </section>

      <section className="status-card wide-card">
        <div className="section-header">
          <div>
            <h2>自选股</h2>
            <p className="section-copy">
              自选股行情来自本地缓存；缺失时会尝试从数据源拉取。
            </p>
          </div>
          <button type="button" className="refresh-button" onClick={loadDashboard}>
            刷新
          </button>
        </div>
        <WatchlistTable
          items={dashboard?.watchlist_summary ?? []}
          loading={loading}
          onOpenStock={onOpenStock}
          onDelete={handleDeleteWatchlist}
        />
      </section>

      <section className="status-card wide-card">
        <h2>市场概览</h2>
        <ul className="stage-list">
          {(dashboard?.market_notes ?? ["市场概览将在后续阶段接入。"]).map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
