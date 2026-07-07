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

export type TimeSharePoint = {
  time: string;
  price: number;
  average_price?: number | null;
  volume?: number | null;
  amount?: number | null;
};

export type TimeShareResponse = {
  code: string;
  name: string;
  source: string;
  points: TimeSharePoint[];
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
  source?: string | null;
  is_live?: boolean;
  cache_time?: string | null;
  quote_time?: string | null;
  is_stale?: boolean;
  cache_age_seconds?: number | null;
};

export type StockPosition = {
  code: string;
  name: string;
  window: number;
  sample_size: number;
  trade_date: string;
  latest_close: number;
  rolling_low: number;
  rolling_high: number;
  position_score: number;
  zone: string;
  label: string;
};

export type MoneyflowBar = {
  date: string;
  main_net_inflow: number;
  main_net_ratio?: number | null;
  super_large_net_inflow?: number | null;
  large_net_inflow?: number | null;
  medium_net_inflow?: number | null;
  small_net_inflow?: number | null;
};

export type MoneyflowResponse = {
  code: string;
  name: string;
  source: string;
  bars: MoneyflowBar[];
};

export type SectorSummary = {
  code: string;
  name: string;
  latest_price?: number | null;
  change_amount?: number | null;
  change_percent?: number | null;
  amount?: number | null;
  main_net_inflow?: number | null;
  market_value?: number | null;
  turnover_rate?: number | null;
  rising_count?: number | null;
  falling_count?: number | null;
  leading_stock?: string | null;
  leading_stock_change_percent?: number | null;
};

export type SectorConstituent = {
  code: string;
  name: string;
  exchange: string;
  latest_price?: number | null;
  change_amount?: number | null;
  change_percent?: number | null;
  volume?: number | null;
  amount?: number | null;
  turnover_rate?: number | null;
  pe_dynamic?: number | null;
  pb?: number | null;
};

export type SectorListResponse = {
  sectors: SectorSummary[];
  source: string;
};

export type SectorDetailResponse = {
  code: string;
  name: string;
  constituents: SectorConstituent[];
  source: string;
};

export type RankingItem = {
  code?: string | null;
  name: string;
  exchange?: string | null;
  latest_price?: number | null;
  change_percent?: number | null;
  amount?: number | null;
  turnover_rate?: number | null;
  main_net_inflow?: number | null;
  market_value?: number | null;
  rising_count?: number | null;
  falling_count?: number | null;
  leading_stock?: string | null;
  leading_stock_change_percent?: number | null;
};

export type RankingGroup = {
  key: string;
  title: string;
  source?: string | null;
  items: RankingItem[];
  error?: string | null;
};

export type DailyReviewResponse = {
  groups: RankingGroup[];
  notes: string[];
};

export type WatchlistItem = {
  id: number;
  code: string;
  name: string;
  exchange: string;
  group_name: string;
  sort_order: number;
  note?: string | null;
  latest_price?: number | null;
  change_amount?: number | null;
  change_percent?: number | null;
  trade_date?: string | null;
  quote_error?: string | null;
  position_score?: number | null;
  position_label?: string | null;
  position_window?: number | null;
  position_error?: string | null;
  main_net_inflow?: number | null;
  main_net_ratio?: number | null;
  moneyflow_date?: string | null;
  moneyflow_error?: string | null;
  source?: string | null;
  is_live?: boolean;
  cache_time?: string | null;
  quote_time?: string | null;
  is_stale?: boolean;
  cache_age_seconds?: number | null;
  created_at: string;
};

export type DashboardResponse = {
  watchlist_count: number;
  watchlist_summary: WatchlistItem[];
  indices: Record<string, unknown>[];
  market_notes: string[];
};
