import type { KlineBar, StockQuote } from "../types/stock";

type QuoteStock = {
  code: string;
  name: string;
  exchange: string;
};

export function buildQuoteFromKline(
  stock: QuoteStock,
  bars: KlineBar[],
): StockQuote | null {
  if (bars.length === 0) {
    return null;
  }

  const latest = bars[bars.length - 1];
  const previous = bars.length > 1 ? bars[bars.length - 2] : null;
  const preClose = previous?.close ?? null;
  const changeAmount =
    preClose !== null ? latest.close - preClose : null;
  const changePercent =
    preClose !== null && preClose !== 0 && changeAmount !== null
      ? (changeAmount / preClose) * 100
      : null;

  return {
    code: stock.code,
    name: stock.name,
    exchange: stock.exchange,
    latest_price: latest.close,
    change_amount: changeAmount,
    change_percent: changePercent,
    open: latest.open,
    high: latest.high,
    low: latest.low,
    pre_close: preClose,
    volume: latest.volume,
    amount: latest.amount,
    turnover_rate: latest.turnover_rate,
    trade_date: latest.date,
  };
}
