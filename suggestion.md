# Builder Suggestion

This file summarizes the latest checker process and gives focused suggestions for the next builder agent. It should be overwritten after every future checker run.

**Last checker run:** 2026-07-03 (fourth run)  
**Scope checked:** Phase 3 price-position / top-bottom zone MVP  
**Source report:** `CHECKER_LOG.md`

---

## Checker Summary

The checker verified the Phase 3 price-position MVP.

Result: **PASS**.

Verified behavior:

- Backend tests pass: 10/10.
- Frontend typecheck passes.
- Frontend production build passes.
- Live `/api/stocks/600519/position?window=250` returns 200 OK.
- Stock detail page displays a Chinese price-position card.
- Watchlist table displays price-position label and score.
- The UI correctly avoids buy/sell signal language.
- No trading, brokerage, account, order, or credential functionality was introduced.

---

## Builder Fix Suggestions

### 1. Tighten K-line cache freshness

`StockService.get_kline()` should verify that cached K-line data reaches the requested `end_date`.

Current behavior mostly checks whether cache exists and whether the cached start date covers the requested start date. This can allow stale cached data to be reused for quote and position calculations.

Suggested fix:

- After reading cached bars, compare the latest cached `trade_date` with the requested `end_date`.
- If cached data is older than the latest expected trade date, fetch again or use a controlled refresh policy.
- Be careful with weekends and holidays; do not assume every calendar day is a trading day.

### 2. Reduce repeated K-line loading

The current flow is functionally correct, but may do repeated work:

- `StockDetail` loads K-line data, then separately loads price-position data.
- `WatchlistService` gets quote data and position data separately for each watchlist item.

Suggested fix:

- Reuse the same K-line series to derive quote and price position where possible.
- Consider a service-level helper that returns quote + position from one K-line lookup.
- For watchlist summaries, consider batching or caching per request to avoid repeated data-source calls.

### 3. Add direct indicator boundary tests

Current tests cover the position endpoint and invalid window rejection. Add unit tests for `calculate_position_score()` / `classify_position_zone()`.

Recommended cases:

- `0-10`: 深度底部区
- `10-20`: 底部观察区
- `20-80`: 中性区
- `80-90`: 高位观察区
- `90-100`: 顶部风险区
- Flat high/low range should return neutral `50.0`.
- Scores should be clamped to `0-100`.

### 4. Keep Phase 3 wording conservative

Continue using wording like:

- 价格位置
- 风险区域
- 底部观察区
- 高位观察区

Avoid wording like:

- 买入
- 卖出
- 建仓
- 清仓
- 交易信号

This keeps the feature aligned with the project boundary: personal market analysis only, not trading advice or automation.

### 5. Dashboard market overview remains later work

The checker confirms this is still acceptable:

- Major indices are not implemented yet.
- Market breadth is not implemented yet.
- Turnover / broader market overview is not implemented yet.

Keep these as later Dashboard expansion tasks unless the user explicitly asks to prioritize them.

---

## Suggested Next Build Direction

Best next technical step: stabilize the price-position data path before adding more indicators.

Recommended order:

1. Improve K-line cache freshness.
2. Refactor quote + position calculations to reuse K-line data.
3. Add direct unit tests for position score boundaries.
4. Then continue toward either Dashboard market overview or Phase 4 money-flow MVP.
