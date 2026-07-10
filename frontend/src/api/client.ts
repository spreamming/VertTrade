import type {
  DashboardResponse,
  DailyReviewResponse,
  KlineResponse,
  MarketOverviewResponse,
  MoneyflowResponse,
  RankingGroup,
  RankingItem,
  SectorDetailResponse,
  SectorKlineResponse,
  SectorListResponse,
  SectorMoneyflowResponse,
  SectorSummary,
  StockPosition,
  StockQuote,
  StockSummary,
  TimeShareResponse,
  WatchlistItem,
} from "../types/stock";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "");

export type HealthResponse = {
  status: string;
  app: string;
  environment: string;
  database: string;
};

export type {
  DashboardResponse,
  DailyReviewResponse,
  KlineResponse,
  MarketOverviewResponse,
  MoneyflowResponse,
  RankingGroup,
  RankingItem,
  SectorDetailResponse,
  SectorKlineResponse,
  SectorListResponse,
  SectorMoneyflowResponse,
  SectorSummary,
  StockPosition,
  StockQuote,
  StockSummary,
  TimeShareResponse,
  WatchlistItem,
};

async function parseErrorMessage(response: Response, path: string): Promise<string> {
  const fallback = `请求失败：${path}`;
  const text = await response.text();

  if (!text) {
    return fallback;
  }

  try {
    const body = JSON.parse(text) as { detail?: string | { msg: string }[] };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      return body.detail[0]?.msg ?? fallback;
    }
  } catch {
    return text;
  }

  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new Error(
      "无法连接后端接口，请确认后端服务已在 8000 端口启动。",
    );
  }

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response, path));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

export async function searchStocks(keyword: string): Promise<StockSummary[]> {
  const params = new URLSearchParams({ keyword });
  return request<StockSummary[]>(`/api/stocks/search?${params.toString()}`);
}

export async function getStockKline(
  code: string,
  refresh = false,
): Promise<KlineResponse> {
  const params = new URLSearchParams();
  if (refresh) {
    params.set("refresh", "true");
  }
  const query = params.toString();
  return request<KlineResponse>(
    `/api/stocks/${code}/kline${query ? `?${query}` : ""}`,
  );
}

export async function getStockIntradayKline(
  code: string,
  period = "1m",
  refresh = false,
): Promise<KlineResponse> {
  const params = new URLSearchParams({ period });
  if (refresh) {
    params.set("refresh", "true");
  }
  return request<KlineResponse>(
    `/api/stocks/${code}/kline/minute?${params.toString()}`,
  );
}

export async function getStockTimeshare(
  code: string,
  refresh = false,
): Promise<TimeShareResponse> {
  const params = new URLSearchParams();
  if (refresh) {
    params.set("refresh", "true");
  }
  const query = params.toString();
  return request<TimeShareResponse>(
    `/api/stocks/${code}/timeshare${query ? `?${query}` : ""}`,
  );
}

export async function getStockQuote(
  code: string,
  refresh = false,
): Promise<StockQuote> {
  const params = new URLSearchParams();
  if (refresh) {
    params.set("refresh", "true");
  }
  const query = params.toString();
  return request<StockQuote>(
    `/api/stocks/${code}/quote${query ? `?${query}` : ""}`,
  );
}

export async function getStockLiveQuote(
  code: string,
  refresh = false,
): Promise<StockQuote> {
  const params = new URLSearchParams();
  if (refresh) {
    params.set("refresh", "true");
  }
  const query = params.toString();
  return request<StockQuote>(
    `/api/stocks/${code}/quote/live${query ? `?${query}` : ""}`,
  );
}

export async function getStockPosition(
  code: string,
  window = 250,
  refresh = false,
): Promise<StockPosition> {
  const params = new URLSearchParams({ window: String(window) });
  if (refresh) {
    params.set("refresh", "true");
  }
  return request<StockPosition>(`/api/stocks/${code}/position?${params.toString()}`);
}

export async function getStockMoneyflow(
  code: string,
  refresh = false,
): Promise<MoneyflowResponse> {
  const params = new URLSearchParams();
  if (refresh) {
    params.set("refresh", "true");
  }
  const query = params.toString();
  return request<MoneyflowResponse>(
    `/api/stocks/${code}/moneyflow${query ? `?${query}` : ""}`,
  );
}

export async function getDashboard(refresh = false): Promise<DashboardResponse> {
  const params = new URLSearchParams();
  if (refresh) {
    params.set("refresh", "true");
  }
  const query = params.toString();
  return request<DashboardResponse>(`/api/dashboard${query ? `?${query}` : ""}`);
}

export async function getMarketOverview(refresh = false): Promise<MarketOverviewResponse> {
  const params = new URLSearchParams();
  if (refresh) {
    params.set("refresh", "true");
  }
  const query = params.toString();
  return request<MarketOverviewResponse>(`/api/market/overview${query ? `?${query}` : ""}`);
}

export async function getDailyReview(): Promise<DailyReviewResponse> {
  return request<DailyReviewResponse>("/api/rankings/daily-review");
}

export async function getIndustrySectors(): Promise<SectorListResponse> {
  return request<SectorListResponse>("/api/sectors/industries");
}

export async function getIndustrySector(
  sector: SectorSummary,
): Promise<SectorDetailResponse> {
  const params = new URLSearchParams({ name: sector.name });
  return request<SectorDetailResponse>(
    `/api/sectors/industries/${sector.code}?${params.toString()}`,
  );
}

export async function getIndustrySectorKline(
  sector: SectorSummary,
): Promise<SectorKlineResponse> {
  const params = new URLSearchParams({ name: sector.name });
  return request<SectorKlineResponse>(
    `/api/sectors/industries/${sector.code}/kline?${params.toString()}`,
  );
}

export async function getIndustrySectorMoneyflow(
  sector: SectorSummary,
): Promise<SectorMoneyflowResponse> {
  const params = new URLSearchParams({ name: sector.name });
  return request<SectorMoneyflowResponse>(
    `/api/sectors/industries/${sector.code}/moneyflow?${params.toString()}`,
  );
}

export async function getWatchlist(): Promise<WatchlistItem[]> {
  return request<WatchlistItem[]>("/api/watchlist");
}

export async function addWatchlistItem(code: string): Promise<WatchlistItem> {
  return request<WatchlistItem>("/api/watchlist", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ code }),
  });
}

export async function deleteWatchlistItem(id: number): Promise<void> {
  await request<void>(`/api/watchlist/${id}`, {
    method: "DELETE",
  });
}
