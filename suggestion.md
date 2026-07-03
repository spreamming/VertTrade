# Builder Suggestion

This file summarizes the latest checker process and gives focused suggestions for the next builder agent. It should be overwritten after every future checker run.

**Last checker run:** 2026-07-03 (fifth run)  
**Scope checked:** Phase 4 individual stock main money-flow MVP  
**Source report:** `CHECKER_LOG.md`

---

## Checker Summary

The checker verified the Phase 4 money-flow MVP.

Result: **PASS with one important risk**.

Verified behavior:

- Backend tests pass: 26/26.
- Frontend typecheck passes.
- Frontend production build passes.
- Money-flow backend model, repository, collector, cache, and API are present.
- Watchlist summary includes latest main net inflow and main net ratio.
- Stock detail includes money-flow summary.
- K-line chart now includes main money-flow bars under volume on the same time axis.
- UI text explains the data source口径 and avoids trading-signal language.
- No trading, brokerage, account, order, or credential functionality was introduced.

Live data-source check:

- `/api/stocks/600519/moneyflow` returned a handled `503` response.
- This means the app did not crash, but live AKShare/Eastmoney money-flow data was unavailable during the check.

---

## Builder Fix Suggestions

### 1. Make money-flow failure non-blocking on stock detail

Current risk:

- `StockDetail` loads K-line, position, and money-flow in one flow.
- If money-flow returns `503`, the page-level catch path prevents available quote/K-line/position data from being set.
- A temporary money-flow failure can therefore make the whole stock detail page look broken.

Suggested fix:

- Load core stock detail data first: K-line, quote, and price position.
- Load money-flow separately.
- If money-flow fails, keep K-line and position visible and show a local money-flow warning near the money-flow panel.
- Do not use one page-level error for optional money-flow data.

### 2. Verify the live AKShare money-flow source

The tests use mocked money-flow data and pass. The live source returned `503`.

Suggested checks:

- Confirm `ak.stock_individual_fund_flow(stock=code, market=market)` still works with current AKShare.
- Confirm `market` should be `sh` / `sz` for the target endpoint.
- Log or inspect missing/changed upstream fields during local debugging.
- Keep the user-facing backend error in Chinese and non-technical.

### 3. Add defensive collector validation

`moneyflow_collector.py` assumes specific Chinese AKShare column names.

Suggested fix:

- Define a required-column list before renaming.
- If required columns are absent, raise a clear data-source error.
- Include enough internal detail for debugging, but do not expose noisy raw provider errors directly to the frontend.

### 4. Keep money-flow cache behavior explicit

The cache refresh behavior is currently basic.

Suggested fix:

- Decide whether money-flow should refresh once per day, on manual refresh, or whenever cached data is stale by date.
- Be careful with weekends and market holidays.
- Keep cached data visible if a refresh fails.

### 5. Preserve the current chart direction

The current UI direction is good:

- K-line, volume, and main money-flow bars share one time axis.
- Money-flow summary stays as a separate explanation/summary panel.

Keep this layout unless the user asks for a separate money-flow chart again.

### 6. Keep wording conservative

Continue using:

- 主力资金流
- 主力净流入
- 主力净占比
- 数据来源 / 数据口径
- 观察维度

Avoid:

- 买入
- 卖出
- 交易信号
- 建仓
- 清仓
- 主力真实动向

Money-flow should remain an observation feature, not a trading instruction.

---

## Suggested Next Build Direction

Best next technical step: improve money-flow resilience before expanding to sector/ranking features.

Recommended order:

1. Decouple money-flow loading from stock detail core data.
2. Add collector column validation and clearer data-source error handling.
3. Confirm live AKShare money-flow behavior with at least one Shanghai and one Shenzhen stock.
4. Add tests for money-flow failure fallback on stock detail/watchlist behavior where practical.
5. Then continue toward sector money-flow or money-flow rankings.
