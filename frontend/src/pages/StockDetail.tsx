import { useCallback, useEffect, useRef, useState } from "react";

import {
  addWatchlistItem,
  deleteWatchlistItem,
  getStockKline,
  getStockIntradayKline,
  getStockLiveQuote,
  getStockMoneyflow,
  getStockPosition,
  getStockTimeshare,
  getWatchlist,
  type KlineResponse,
  type MoneyflowResponse,
  type StockPosition,
  type StockQuote,
  type StockSummary,
  type TimeShareResponse,
  type WatchlistItem,
} from "../api/client";
import { KLineChart } from "../components/KLineChart";
import { MoneyFlowPanel } from "../components/MoneyFlowPanel";
import { PositionCard } from "../components/PositionCard";
import { TimeShareChart } from "../components/TimeShareChart";
import { buildQuoteFromKline } from "../utils/quote";

type StockDetailProps = {
  stock: StockSummary;
  onBack: () => void;
};

const KLINE_PERIODS = [
  { value: "timeshare", label: "分时" },
  { value: "daily", label: "日 K" },
  { value: "1m", label: "1 分" },
  { value: "5m", label: "5 分" },
  { value: "15m", label: "15 分" },
  { value: "30m", label: "30 分" },
  { value: "60m", label: "60 分" },
];

function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) {
    return "--";
  }
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "--";
  }
  return new Date(value).toLocaleString("zh-CN", {
    hour12: false,
  });
}

function formatCacheAge(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "--";
  }
  return `${Math.round(value)} 秒`;
}

export function StockDetail({ stock, onBack }: StockDetailProps) {
  const didInitialKlineLoadRef = useRef(false);
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [kline, setKline] = useState<KlineResponse | null>(null);
  const [timeshare, setTimeshare] = useState<TimeShareResponse | null>(null);
  const [klinePeriod, setKlinePeriod] = useState("daily");
  const [position, setPosition] = useState<StockPosition | null>(null);
  const [moneyflow, setMoneyflow] = useState<MoneyflowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [klineLoading, setKlineLoading] = useState(false);
  const [positionLoading, setPositionLoading] = useState(false);
  const [moneyflowLoading, setMoneyflowLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [moneyflowError, setMoneyflowError] = useState<string | null>(null);
  const [liveQuoteError, setLiveQuoteError] = useState<string | null>(null);
  const [watchlistItem, setWatchlistItem] = useState<WatchlistItem | null>(null);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  const [watchlistMessage, setWatchlistMessage] = useState<string | null>(null);
  const [watchlistError, setWatchlistError] = useState<string | null>(null);

  const loadWatchlistState = useCallback(async () => {
    setWatchlistError(null);

    try {
      const items = await getWatchlist();
      setWatchlistItem(items.find((item) => item.code === stock.code) ?? null);
    } catch (err: unknown) {
      setWatchlistError(err instanceof Error ? err.message : "加载自选股状态失败");
    }
  }, [stock.code]);

  const loadKline = useCallback(
    async (refresh = false) => {
      setKlineLoading(true);
      setError(null);

      try {
        if (klinePeriod === "timeshare") {
          const timeshareData = await getStockTimeshare(stock.code);
          setTimeshare(timeshareData);
          if (timeshareData.points.length > 0) {
            const latest = timeshareData.points[timeshareData.points.length - 1];
            setQuote((current) =>
              current ? { ...current, latest_price: latest.price } : current,
            );
          }
          return;
        }

        const klineData =
          klinePeriod === "daily"
            ? await getStockKline(stock.code, refresh)
            : await getStockIntradayKline(stock.code, klinePeriod);
        const quoteData = buildQuoteFromKline(stock, klineData.bars);

        if (!quoteData) {
          throw new Error(`暂无 ${stock.code} 的行情数据`);
        }

        setQuote(quoteData);
        setKline(klineData);
        setTimeshare(null);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "加载图表数据失败");
      } finally {
        setKlineLoading(false);
      }
    },
    [klinePeriod, stock.code],
  );

  const loadPosition = useCallback(
    async (refresh = false) => {
      setPositionLoading(true);

      try {
        setPosition(await getStockPosition(stock.code, 250, refresh));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "加载价格位置失败");
      } finally {
        setPositionLoading(false);
      }
    },
    [stock.code],
  );

  const loadMoneyflow = useCallback(
    async (refresh = false) => {
      setMoneyflowLoading(true);
      setMoneyflowError(null);
      setMoneyflow(null);

      try {
        const moneyflowData = await getStockMoneyflow(stock.code, refresh);
        setMoneyflow(moneyflowData);
      } catch (err: unknown) {
        setMoneyflowError(
          err instanceof Error ? err.message : "加载主力资金流失败",
        );
      } finally {
        setMoneyflowLoading(false);
      }
    },
    [stock.code],
  );

  async function loadAllData(refresh = false) {
    setLoading(true);
    await Promise.all([
      loadKline(refresh),
      loadPosition(refresh),
      loadMoneyflow(refresh),
    ]);
    setLoading(false);
  }

  useEffect(() => {
    void loadAllData();
    // Initial stock load only; period changes are handled by the kline-only effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stock.code]);

  useEffect(() => {
    if (!didInitialKlineLoadRef.current) {
      didInitialKlineLoadRef.current = true;
      return;
    }
    void loadKline(false);
  }, [loadKline]);

  useEffect(() => {
    void loadWatchlistState();
  }, [loadWatchlistState]);

  useEffect(() => {
    let cancelled = false;
    let inFlight = false;

    async function loadLiveQuote() {
      if (inFlight) {
        return;
      }
      inFlight = true;
      try {
        const liveQuote = await getStockLiveQuote(stock.code);
        if (!cancelled) {
          setQuote(liveQuote);
          setLiveQuoteError(null);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setLiveQuoteError(
            err instanceof Error ? err.message : "实时行情刷新失败",
          );
        }
      } finally {
        inFlight = false;
      }
    }

    void loadLiveQuote();
    const intervalId = window.setInterval(() => {
      void loadLiveQuote();
    }, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [stock.code]);

  const changeClass =
    quote?.change_percent !== null &&
    quote?.change_percent !== undefined &&
    quote.change_percent >= 0
      ? "quote-up"
      : "quote-down";

  async function handleToggleWatchlist() {
    setWatchlistLoading(true);
    setWatchlistMessage(null);
    setWatchlistError(null);

    try {
      if (watchlistItem) {
        await deleteWatchlistItem(watchlistItem.id);
        setWatchlistItem(null);
        setWatchlistMessage(`${stock.name} 已从自选股移除`);
      } else {
        const created = await addWatchlistItem(stock.code);
        setWatchlistItem(created);
        setWatchlistMessage(`${stock.name} 已加入自选股`);
      }
    } catch (err: unknown) {
      setWatchlistError(err instanceof Error ? err.message : "更新自选股失败");
    } finally {
      setWatchlistLoading(false);
    }
  }

  return (
    <div className="stock-detail">
      <header className="stock-header">
        <button type="button" className="back-button" onClick={onBack}>
          返回
        </button>
        <div>
          <p className="eyebrow">
            {stock.code} · {stock.exchange}
          </p>
          <h1>{stock.name}</h1>
        </div>
        <div className="stock-header-actions">
          <button
            type="button"
            className={watchlistItem ? "watchlist-active-button" : "refresh-button"}
            onClick={() => void handleToggleWatchlist()}
            disabled={watchlistLoading}
          >
            {watchlistItem ? "已在自选 · 移除" : "加入自选"}
          </button>
          <button
            type="button"
            className="refresh-button"
            onClick={() => void loadAllData(true)}
            disabled={loading || moneyflowLoading}
          >
            刷新
          </button>
        </div>
      </header>

      {(loading || klineLoading) && !quote ? <p className="loading-text">正在加载行情数据...</p> : null}
      {error ? <p className="search-error">{error}</p> : null}
      {liveQuoteError ? <p className="table-note">{liveQuoteError}</p> : null}
      {watchlistMessage ? <p className="success-text">{watchlistMessage}</p> : null}
      {watchlistError ? <p className="search-error">{watchlistError}</p> : null}

      {quote ? (
        <section className="quote-grid">
          <div>
            <dt>最新价</dt>
            <dd className={changeClass}>{formatNumber(quote.latest_price)}</dd>
          </div>
          <div>
            <dt>涨跌</dt>
            <dd className={changeClass}>
              {formatNumber(quote.change_amount)} ({formatNumber(quote.change_percent)}%)
            </dd>
          </div>
          <div>
            <dt>成交量</dt>
            <dd>{formatNumber(quote.volume, 0)}</dd>
          </div>
          <div>
            <dt>成交额</dt>
            <dd>{formatNumber(quote.amount, 0)}</dd>
          </div>
          <div>
            <dt>换手率</dt>
            <dd>{formatNumber(quote.turnover_rate)}%</dd>
          </div>
          <div>
            <dt>交易日期</dt>
            <dd>{quote.trade_date}</dd>
          </div>
          <div>
            <dt>行情状态</dt>
            <dd>
              {quote.is_live
                ? quote.is_stale
                  ? "缓存行情"
                  : "近实时"
                : "日线缓存"}
            </dd>
          </div>
          <div>
            <dt>行情时间</dt>
            <dd>{formatDateTime(quote.quote_time)}</dd>
          </div>
          <div>
            <dt>刷新时间</dt>
            <dd>{formatDateTime(quote.cache_time)}</dd>
          </div>
          <div>
            <dt>缓存年龄</dt>
            <dd>{quote.is_stale ? formatCacheAge(quote.cache_age_seconds) : "--"}</dd>
          </div>
        </section>
      ) : null}

      <PositionCard position={position} loading={loading || positionLoading} />

      {klinePeriod === "timeshare" && timeshare && timeshare.points.length > 0 ? (
        <section className="chart-panel">
          <div className="section-header">
            <div>
              <h2>分时图</h2>
              <p className="section-copy">
                分时图展示盘中价格线、均价线和成交量，仅用于行情观察。
              </p>
            </div>
            <div className="period-switcher">
              {KLINE_PERIODS.map((period) => (
                <button
                  key={period.value}
                  type="button"
                  className={period.value === klinePeriod ? "period-active" : ""}
                  onClick={() => setKlinePeriod(period.value)}
                >
                  {period.label}
                </button>
              ))}
            </div>
          </div>
          <TimeShareChart points={timeshare.points} />
        </section>
      ) : null}

      {klinePeriod !== "timeshare" && kline && kline.bars.length > 0 ? (
        <section className="chart-panel">
          <div className="section-header">
            <div>
              <h2>{klinePeriod === "daily" ? "日 K 线" : "分钟 K 线"}</h2>
              <p className="section-copy">
                {klinePeriod === "daily"
                  ? "日 K 线下方显示成交量和主力资金流。"
                  : "分钟 K 用于盘中观察，当前先显示价格和成交量。"}
              </p>
            </div>
            <div className="period-switcher">
              {KLINE_PERIODS.map((period) => (
                <button
                  key={period.value}
                  type="button"
                  className={period.value === klinePeriod ? "period-active" : ""}
                  onClick={() => setKlinePeriod(period.value)}
                >
                  {period.label}
                </button>
              ))}
            </div>
          </div>
          <KLineChart
            bars={kline.bars}
            moneyflowBars={klinePeriod === "daily" ? moneyflow?.bars ?? [] : []}
          />
        </section>
      ) : null}

      <MoneyFlowPanel
        moneyflow={moneyflow}
        loading={moneyflowLoading}
        error={moneyflowError}
      />
    </div>
  );
}
