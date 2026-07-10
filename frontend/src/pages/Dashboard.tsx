import { useCallback, useEffect, useMemo, useState } from "react";

import {
  addWatchlistItem,
  deleteWatchlistItem,
  getDashboard,
  getDailyReview,
  getIndustrySectors,
  getMarketOverview,
  getStockLiveQuote,
  type DashboardResponse,
  type DailyReviewResponse,
  type MarketOverviewResponse,
  type SectorSummary,
  type StockQuote,
  type StockSummary,
  type WatchlistItem,
} from "../api/client";
import { MarketOverviewPanel } from "../components/MarketOverviewPanel";
import { SearchBox } from "../components/SearchBox";
import { SectorPanel } from "../components/SectorPanel";
import { RankingPanel } from "../components/RankingPanel";
import { WatchlistTable } from "../components/WatchlistTable";
import { WatchlistReviewPanel } from "../components/WatchlistReviewPanel";

type DashboardProps = {
  onOpenStock: (stock: StockSummary) => void;
  onOpenSector: (sector: SectorSummary) => void;
};

const MAX_AUTO_REFRESH_WATCHLIST = 20;
const DASHBOARD_CACHE_KEY = "verttrade:lastDashboard";
const MARKET_OVERVIEW_CACHE_KEY = "verttrade:lastMarketOverview";
const SECTOR_CACHE_KEY = "verttrade:lastIndustrySectors";
const REVIEW_CACHE_KEY = "verttrade:lastDailyReview";
const BACKGROUND_RETRY_MS = 15000;

function readStoredValue<T>(key: string): T | null {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function writeStoredValue<T>(key: string, value: T): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Browser storage is best-effort; live UI should keep working without it.
  }
}

function groupHasItems(group: DailyReviewResponse["groups"][number]): boolean {
  return group.items.length > 0;
}

function mergeReviewWithPrevious(
  incoming: DailyReviewResponse,
  previous: DailyReviewResponse | null,
): DailyReviewResponse {
  if (!previous) {
    return incoming;
  }

  const previousGroups = new Map(previous.groups.map((group) => [group.key, group]));
  const groups = incoming.groups.map((group) => {
    const previousGroup = previousGroups.get(group.key);
    if ((group.error || !groupHasItems(group)) && previousGroup && groupHasItems(previousGroup)) {
      return previousGroup;
    }
    return group;
  });

  const preservedCount = groups.filter((group, index) => group !== incoming.groups[index]).length;
  const notes =
    preservedCount > 0
      ? [
          ...incoming.notes,
          `部分榜单刷新失败，已保留 ${preservedCount} 个上次成功榜单。`,
        ]
      : incoming.notes;

  return { ...incoming, groups, notes };
}

function readStoredSectors(): { sectors: SectorSummary[]; source: string } | null {
  return readStoredValue<{ sectors: SectorSummary[]; source: string }>(
    SECTOR_CACHE_KEY,
  );
}

export function Dashboard({ onOpenStock, onOpenSector }: DashboardProps) {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(() =>
    readStoredValue<DashboardResponse>(DASHBOARD_CACHE_KEY),
  );
  const [marketOverview, setMarketOverview] = useState<MarketOverviewResponse | null>(() =>
    readStoredValue<MarketOverviewResponse>(MARKET_OVERVIEW_CACHE_KEY)
      ?? readStoredValue<DashboardResponse>(DASHBOARD_CACHE_KEY)?.market_overview
      ?? null,
  );
  const [dailyReview, setDailyReview] = useState<DailyReviewResponse | null>(() =>
    readStoredValue<DailyReviewResponse>(REVIEW_CACHE_KEY),
  );
  const [liveQuotes, setLiveQuotes] = useState<Record<string, StockQuote>>({});
  const [sectors, setSectors] = useState<SectorSummary[]>(() => {
    return readStoredSectors()?.sectors ?? [];
  });
  const [sectorSource, setSectorSource] = useState<string | null>(() => {
    return readStoredSectors()?.source ?? null;
  });
  const [loading, setLoading] = useState(() => {
    return readStoredValue<DashboardResponse>(DASHBOARD_CACHE_KEY) === null;
  });
  const [marketOverviewLoading, setMarketOverviewLoading] = useState(() => {
    return readStoredValue<MarketOverviewResponse>(MARKET_OVERVIEW_CACHE_KEY) === null
      && readStoredValue<DashboardResponse>(DASHBOARD_CACHE_KEY)?.market_overview == null;
  });
  const [reviewLoading, setReviewLoading] = useState(() => {
    return readStoredValue<DailyReviewResponse>(REVIEW_CACHE_KEY) === null;
  });
  const [sectorsLoading, setSectorsLoading] = useState(() => {
    return readStoredSectors() === null;
  });
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [marketOverviewError, setMarketOverviewError] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [sectorsError, setSectorsError] = useState<string | null>(null);
  const [dashboardRetrying, setDashboardRetrying] = useState(false);
  const [reviewRetrying, setReviewRetrying] = useState(false);
  const [sectorsRetrying, setSectorsRetrying] = useState(false);

  const loadDashboard = useCallback(async (background = false) => {
    if (background) {
      setDashboardRetrying(true);
    } else {
      setLoading(true);
      setError(null);
    }

    try {
      const response = await getDashboard();
      setDashboard(response);
      setMarketOverview(response.market_overview);
      writeStoredValue(DASHBOARD_CACHE_KEY, response);
      writeStoredValue(MARKET_OVERVIEW_CACHE_KEY, response.market_overview);
      setError(null);
      setMarketOverviewError(null);
    } catch (err: unknown) {
      const cached = readStoredValue<DashboardResponse>(DASHBOARD_CACHE_KEY);
      if (cached) {
        setDashboard(cached);
        setError("自选股刷新失败，已显示上次成功数据。");
      } else {
        setError(err instanceof Error ? err.message : "加载首页数据失败");
      }
    } finally {
      if (background) {
        setDashboardRetrying(false);
      } else {
        setLoading(false);
      }
    }
  }, []);

  const loadMarketOverview = useCallback(async (refresh = false, background = false) => {
    if (!background) {
      setMarketOverviewLoading(true);
      setMarketOverviewError(null);
    }

    try {
      const response = await getMarketOverview(refresh);
      setMarketOverview(response);
      writeStoredValue(MARKET_OVERVIEW_CACHE_KEY, response);
      setMarketOverviewError(null);
    } catch (err: unknown) {
      const cached = readStoredValue<MarketOverviewResponse>(MARKET_OVERVIEW_CACHE_KEY);
      if (cached) {
        setMarketOverview(cached);
        setMarketOverviewError("市场概览刷新失败，已显示上次成功数据。");
      } else {
        setMarketOverviewError(err instanceof Error ? err.message : "加载市场概览失败");
      }
    } finally {
      if (!background) {
        setMarketOverviewLoading(false);
      }
    }
  }, []);

  const loadDailyReview = useCallback(async (background = false) => {
    if (background) {
      setReviewRetrying(true);
    } else {
      setReviewLoading(true);
      setReviewError(null);
    }

    try {
      const response = await getDailyReview();
      setDailyReview((current) => {
        const cached = current ?? readStoredValue<DailyReviewResponse>(REVIEW_CACHE_KEY);
        const merged = mergeReviewWithPrevious(response, cached);
        writeStoredValue(REVIEW_CACHE_KEY, merged);
        return merged;
      });
      setReviewError(null);
    } catch (err: unknown) {
      const cached = readStoredValue<DailyReviewResponse>(REVIEW_CACHE_KEY);
      if (cached) {
        setDailyReview(cached);
        setReviewError("排行榜刷新失败，已显示上次成功数据。");
      } else {
        setReviewError(err instanceof Error ? err.message : "加载排行榜失败");
      }
    } finally {
      if (background) {
        setReviewRetrying(false);
      } else {
        setReviewLoading(false);
      }
    }
  }, []);

  const loadSectors = useCallback(async (background = false) => {
    if (background) {
      setSectorsRetrying(true);
    } else {
      setSectorsLoading(true);
      setSectorsError(null);
    }

    try {
      const response = await getIndustrySectors();
      setSectors(response.sectors);
      setSectorSource(response.source);
      writeStoredValue(SECTOR_CACHE_KEY, response);
      setSectorsError(null);
    } catch (err: unknown) {
      const cached = readStoredValue<{ sectors: SectorSummary[]; source: string }>(
        SECTOR_CACHE_KEY,
      );
      if (cached) {
        setSectors(cached.sectors);
        setSectorSource(cached.source);
        setSectorsError("行业板块刷新失败，已显示上次成功数据。");
      } else {
        setSectorsError(err instanceof Error ? err.message : "加载行业板块失败");
        setSectorSource(null);
      }
    } finally {
      if (background) {
        setSectorsRetrying(false);
      } else {
        setSectorsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void loadDashboard(dashboard !== null);
    void loadMarketOverview(marketOverview !== null, marketOverview !== null);
    void loadDailyReview(dailyReview !== null);
    void loadSectors(sectors.length > 0);
    // Initial load only. Cached ranking/sector data should render immediately;
    // fresh data is fetched in the background and replaces it when available.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void loadMarketOverview(false, true);
    }, 15000);

    return () => window.clearInterval(intervalId);
  }, [loadMarketOverview]);

  useEffect(() => {
    if (!error && !reviewError && !sectorsError && !marketOverviewError) {
      return;
    }

    const intervalId = window.setInterval(() => {
      if (error) {
        void loadDashboard(true);
      }
      if (marketOverviewError) {
        void loadMarketOverview(false, true);
      }
      if (reviewError) {
        void loadDailyReview(true);
      }
      if (sectorsError) {
        void loadSectors(true);
      }
    }, BACKGROUND_RETRY_MS);

    return () => window.clearInterval(intervalId);
  }, [
    error,
    loadDashboard,
    loadDailyReview,
    loadMarketOverview,
    loadSectors,
    marketOverviewError,
    reviewError,
    sectorsError,
  ]);

  useEffect(() => {
    const items = dashboard?.watchlist_summary ?? [];
    if (items.length === 0) {
      return;
    }

    let cancelled = false;
    let inFlight = false;

    async function refreshLiveQuotes() {
      if (inFlight) {
        return;
      }
      inFlight = true;
      const refreshItems = items.slice(0, MAX_AUTO_REFRESH_WATCHLIST);
      try {
        const results = await Promise.allSettled(
          refreshItems.map(async (item) => ({
            code: item.code,
            quote: await getStockLiveQuote(item.code),
          })),
        );
        if (cancelled) {
          return;
        }
        setLiveQuotes((current) => {
          const next = { ...current };
          for (const result of results) {
            if (result.status === "fulfilled") {
              next[result.value.code] = result.value.quote;
            }
          }
          return next;
        });
      } finally {
        inFlight = false;
      }
    }

    void refreshLiveQuotes();
    const intervalId = window.setInterval(() => {
      void refreshLiveQuotes();
    }, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [dashboard?.watchlist_summary]);

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

  const watchlistSummary = useMemo<WatchlistItem[]>(() => {
    return (dashboard?.watchlist_summary ?? []).map((item) => {
      const liveQuote = liveQuotes[item.code];
      if (!liveQuote) {
        return item;
      }

      return {
        ...item,
        latest_price: liveQuote.latest_price,
        change_amount: liveQuote.change_amount,
        change_percent: liveQuote.change_percent,
        trade_date: liveQuote.trade_date,
        source: liveQuote.source,
        is_live: liveQuote.is_live,
        cache_time: liveQuote.cache_time,
        quote_time: liveQuote.quote_time,
        is_stale: liveQuote.is_stale,
        cache_age_seconds: liveQuote.cache_age_seconds,
      };
    });
  }, [dashboard?.watchlist_summary, liveQuotes]);

  return (
    <main className="app-shell dashboard-shell">
      <section className="hero">
        <p className="eyebrow">个人 A 股看盘工具</p>
        <h1>VertTrade</h1>
        <p>
          首页用于维护自选股，并快速查看大盘指数、市场广度、行业板块和每日复盘。
        </p>
      </section>

      <MarketOverviewPanel
        overview={marketOverview}
        loading={marketOverviewLoading}
        error={marketOverviewError}
        onRefresh={() => void loadMarketOverview(true, false)}
      />

      <section className="dashboard-grid">
        <div className="status-card">
          <h2>添加自选股</h2>
          <p className="section-copy">
            搜索股票后点击结果，即可加入自选股。点击表格里的股票名称可进入个股详情页。
          </p>
          <SearchBox onSelect={handleAddWatchlist} />
          {actionMessage ? <p className="success-text">{actionMessage}</p> : null}
          {error ? (
            <p className="search-error">
              {dashboardRetrying ? `${error} 正在后台重试...` : error}
            </p>
          ) : null}
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
              自选股行情会近实时刷新；为保护免费数据源，自动刷新前 {MAX_AUTO_REFRESH_WATCHLIST} 条。
            </p>
          </div>
          <button
            type="button"
            className="refresh-button"
            onClick={() => void loadDashboard(false)}
          >
            刷新
          </button>
        </div>
        <WatchlistTable
          items={watchlistSummary}
          loading={loading}
          onOpenStock={onOpenStock}
          onDelete={handleDeleteWatchlist}
        />
      </section>

      <WatchlistReviewPanel items={watchlistSummary} />

      <RankingPanel
        review={dailyReview}
        loading={reviewLoading}
        error={
          reviewRetrying && reviewError
            ? `${reviewError} 正在后台重试...`
            : reviewError
        }
        onRefresh={loadDailyReview}
        onOpenStock={onOpenStock}
        onOpenSector={onOpenSector}
      />

      <SectorPanel
        sectors={sectors}
        loading={sectorsLoading}
        error={
          sectorsRetrying && sectorsError
            ? `${sectorsError} 正在后台重试...`
            : sectorsError
        }
        source={sectorSource}
        onRefresh={loadSectors}
        onOpenSector={onOpenSector}
      />
    </main>
  );
}
