import { useCallback, useEffect, useState } from "react";

import {
  getStockKline,
  getStockMoneyflow,
  getStockPosition,
  type KlineResponse,
  type MoneyflowResponse,
  type StockPosition,
  type StockQuote,
  type StockSummary,
} from "../api/client";
import { KLineChart } from "../components/KLineChart";
import { MoneyFlowPanel } from "../components/MoneyFlowPanel";
import { PositionCard } from "../components/PositionCard";
import { buildQuoteFromKline } from "../utils/quote";

type StockDetailProps = {
  stock: StockSummary;
  onBack: () => void;
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

export function StockDetail({ stock, onBack }: StockDetailProps) {
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [kline, setKline] = useState<KlineResponse | null>(null);
  const [position, setPosition] = useState<StockPosition | null>(null);
  const [moneyflow, setMoneyflow] = useState<MoneyflowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [moneyflowLoading, setMoneyflowLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [moneyflowError, setMoneyflowError] = useState<string | null>(null);

  const loadData = useCallback(
    async (refresh = false) => {
      setLoading(true);
      setError(null);
      setMoneyflowLoading(true);
      setMoneyflowError(null);
      setMoneyflow(null);

      try {
        const [klineData, positionData] = await Promise.all([
          getStockKline(stock.code, refresh),
          getStockPosition(stock.code, 250, refresh),
        ]);
        const quoteData = buildQuoteFromKline(stock, klineData.bars);

        if (!quoteData) {
          throw new Error(`暂无 ${stock.code} 的行情数据`);
        }

        setQuote(quoteData);
        setKline(klineData);
        setPosition(positionData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "加载个股数据失败");
      } finally {
        setLoading(false);
      }

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

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const changeClass =
    quote?.change_percent !== null &&
    quote?.change_percent !== undefined &&
    quote.change_percent >= 0
      ? "quote-up"
      : "quote-down";

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
        <button
          type="button"
          className="refresh-button"
          onClick={() => void loadData(true)}
          disabled={loading || moneyflowLoading}
        >
          刷新
        </button>
      </header>

      {loading && !quote ? <p className="loading-text">正在加载行情数据...</p> : null}
      {error ? <p className="search-error">{error}</p> : null}

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
        </section>
      ) : null}

      <PositionCard position={position} loading={loading} />

      {kline && kline.bars.length > 0 ? (
        <section className="chart-panel">
          <h2>日 K 线 / 成交量 / 主力资金流</h2>
          <KLineChart bars={kline.bars} moneyflowBars={moneyflow?.bars ?? []} />
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
