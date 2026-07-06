# Builder Suggestion

This file summarizes the latest checker process and gives focused suggestions for the next builder agent. It should be overwritten after every future checker run.

**Last checker run:** 2026-07-06 (ninth run)  
**Current stage checked:** Stage 8 realtime market watch MVP  
**Source report:** `CHECKER_LOG.md`

---

## Checker Summary

The checker verified the current local stage: Stage 8 realtime market watch MVP.

Result: **PASS**.

Verified behavior:

- Backend tests pass: 39/39.
- Frontend typecheck passes.
- Frontend production build passes.
- `/api/stocks/600519/quote/live?refresh=true` returns 200.
- `/api/stocks/000001/quote/live?refresh=true` returns 200.
- Live quote responses include `is_live`, `source`, `quote_time`, and `cache_time`.
- Stock detail polls live quotes every 3 seconds.
- Watchlist live refresh polls every 5 seconds.
- Watchlist review summary is present.
- Daily review endpoint still returns all 8 ranking groups.
- Project remains a personal market observation app, not a trading platform.

---

## Builder Fix Suggestions

### 1. Update provider wording in docs

The implementation now prefers Tencent live quote data and uses Eastmoney as fallback.

Suggested updates:

- Update `market_watch_development_plan.md` Stage 8 status text.
- Update `README.md` current app flow to mention realtime quote refresh, ranking review, sectors, and watchlist review summary.
- Keep the wording as “近实时” rather than “实时” to avoid overstating provider freshness.

### 2. Add stale/fallback status for live quotes

Backend can return cached live quotes if provider refresh fails and a cached value exists.

Suggested improvement:

- Add a field such as `is_stale` or `cache_age_seconds`.
- Show a small UI label when quote data is served from cache after provider failure.
- Keep `quote_time` and `cache_time` visible.

### 3. Protect watchlist polling from large lists

Dashboard currently requests live quotes for every watchlist item every 5 seconds.

Suggested guardrails:

- Cap the number of auto-refreshed watchlist rows.
- Batch requests if a backend batch endpoint is added later.
- Add backoff when repeated live quote refreshes fail.
- Keep manual refresh available.

### 4. Add manual or automated realtime UI verification

Backend tests cover the live quote endpoint, but browser behavior is not covered.

Suggested checks:

- Stock detail updates latest quote without reloading the whole page.
- Watchlist latest price and change percent update after the polling interval.
- Provider quote time and local refresh time are visible.
- Live quote failure shows a local warning and does not break K-line, position, or money-flow panels.

### 5. Keep Stage 8 MVP scope focused

Current Stage 8 MVP is enough for near-realtime quote observation.

Defer unless explicitly requested:

- Minute K-line.
- Time-sharing chart.
- WebSocket/SSE push.
- Tick or Level-2 data.
- Complex realtime alerts.

### 6. Keep wording observational

Continue using:

- 近实时
- 行情观察
- 刷新时间
- 行情时间
- 观察维度

Avoid:

- 买入
- 卖出
- 建仓
- 清仓
- 交易信号
- 下单

Realtime data should support market watching, not trading execution.

---

## Suggested Next Build Direction

Best next technical step: polish realtime quote reliability and user feedback before adding realtime charts.

Recommended order:

1. Update docs to match Tencent-first live quote behavior.
2. Add stale/cache-age metadata for live quote responses.
3. Add watchlist polling guardrails for larger lists.
4. Do a browser smoke test for stock detail and watchlist polling.
5. Then consider minute K-line or time-sharing chart as the next realtime enhancement.
