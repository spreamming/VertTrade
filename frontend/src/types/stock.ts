export type StockSummary = {
  code: string;
  name: string;
  exchange: string;
};

export type KlineBar = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  turnover_rate?: number | null;
};

export type KlineResponse = {
  code: string;
  name: string;
  period: string;
  bars: KlineBar[];
};

export type StockQuote = {
  code: string;
  name: string;
  exchange: string;
  latest_price: number;
  change_amount?: number | null;
  change_percent?: number | null;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  pre_close?: number | null;
  volume?: number | null;
  amount?: number | null;
  turnover_rate?: number | null;
  trade_date: string;
};
