import { useEffect, useState } from "react";

import { searchStocks, type StockSummary } from "../api/client";

type SearchBoxProps = {
  onSelect: (stock: StockSummary) => void;
};

export function SearchBox({ onSelect }: SearchBoxProps) {
  const [keyword, setKeyword] = useState("");
  const [results, setResults] = useState<StockSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const trimmed = keyword.trim();
    if (trimmed.length < 1) {
      setResults([]);
      setError(null);
      return;
    }

    const timer = window.setTimeout(() => {
      setLoading(true);
      searchStocks(trimmed)
        .then(setResults)
        .catch((err: unknown) => {
          setResults([]);
          setError(err instanceof Error ? err.message : "搜索失败");
        })
        .finally(() => setLoading(false));
    }, 300);

    return () => window.clearTimeout(timer);
  }, [keyword]);

  return (
    <div className="search-box">
      <label htmlFor="stock-search">搜索 A 股</label>
      <input
        id="stock-search"
        type="search"
        placeholder="输入股票代码或名称，例如 600519 或 贵州茅台"
        value={keyword}
        onChange={(event) => setKeyword(event.target.value)}
        autoComplete="off"
      />
      {loading ? <p className="search-meta">正在搜索...</p> : null}
      {error ? <p className="search-error">{error}</p> : null}
      {results.length > 0 ? (
        <ul className="search-results">
          {results.map((stock) => (
            <li key={stock.code}>
              <button type="button" onClick={() => onSelect(stock)}>
                <span>{stock.name}</span>
                <span>
                  {stock.code} · {stock.exchange}
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
