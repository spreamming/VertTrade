import type { KlineResponse, StockQuote, StockSummary } from "../types/stock";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export type HealthResponse = {
  status: string;
  app: string;
  environment: string;
  database: string;
};

export type { KlineResponse, StockQuote, StockSummary };

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

async function request<T>(path: string): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`);
  } catch {
    throw new Error(
      "无法连接后端接口，请确认后端服务已在 8000 端口启动。",
    );
  }

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response, path));
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
