# Builder Suggestion

This file summarizes the latest checker process and gives focused suggestions for the next builder agent. It should be overwritten after every future checker run.

**Last checker run:** 2026-07-03 (sixth run)  
**Scope checked:** Phase 5 industry sector MVP  
**Source report:** `CHECKER_LOG.md`

---

## Checker Summary

The checker verified the Phase 5 industry sector MVP.

Result: **PASS with one important data-source gap**.

Verified behavior:

- Backend tests pass: 31/31.
- Frontend typecheck passes.
- Frontend production build passes.
- Industry sector list API is mounted and works.
- Dashboard displays an industry sector panel.
- Sector detail page exists and supports constituent click-through to stock detail.
- Collector validates required provider columns.
- Eastmoney sector list has a Tonghuashun fallback.
- Chinese UI is maintained.
- No trading, brokerage, account, order, or credential functionality was introduced.

Live data-source check:

- `/api/sectors/industries` returned 200 and sector rows.
- `/api/sectors/industries/BK1408?name=机器人` returned a handled 503 for constituents.

The sector list workflow is usable live. The sector detail constituent workflow is still provider-fragile.

---

## Builder Fix Suggestions

### 1. Stabilize sector constituent detail

Current issue:

- Sector list works live.
- Sector detail returns `503` for a live sector constituent request.
- The frontend shows an error, but the core Phase 5 detail workflow is not reliable yet.

Suggested fix:

- Re-check `ak.stock_board_industry_cons_em(symbol=...)` input requirements.
- Try both sector name and sector code when fetching constituents.
- If Eastmoney detail remains unstable, look for a Tonghuashun constituent fallback to match the sector-list fallback.
- Keep the current Chinese 503 message, but add internal debug detail during local development.

### 2. Return accurate data-source metadata

Current issue:

- `SectorListResponse.source` defaults to `akshare_em`.
- If the Tonghuashun fallback supplies sector rows, the response can still report the Eastmoney source.

Suggested fix:

- Have the collector return both the normalized frame and a source identifier.
- Use values like `akshare_em` and `akshare_ths`.
- Surface this source in `SectorListResponse` and, if useful, in the Dashboard sector panel.

### 3. Add an empty-state for sector detail

Current issue:

- If sector detail succeeds but returns zero constituents, the page has no clear empty-state text.

Suggested fix:

- In `SectorDetail`, show a Chinese message such as `暂无成分股数据。`
- Keep this separate from the error state so users can distinguish empty data from provider failure.

### 4. Consider lightweight sector caching

Current issue:

- Sector list and constituents are live-provider dependent.
- Dashboard sector panel can fail whenever the upstream source is slow or unavailable.

Suggested fix:

- Add a short-lived local cache for sector list first.
- Keep stale sector list visible when refresh fails.
- Defer full historical sector storage until the sector workflow stabilizes.

### 5. Keep Phase 5 scope focused

Do not expand too far before stabilizing the current sector workflow.

Good next work:

- Reliable sector list.
- Reliable sector constituents.
- Click-through to stock detail.
- Clear provider/source labeling.

Defer:

- Full sector K-line history.
- Historical sector money-flow chart.
- Sector rankings page.
- Complex review workflows.

### 6. Keep wording observational

Continue using:

- 行业板块
- 成分股
- 板块强弱
- 资金流观察
- 数据来源 / 数据口径

Avoid wording that turns sector information into trading instructions:

- 买入
- 卖出
- 建仓
- 清仓
- 交易信号

---

## Suggested Next Build Direction

Best next technical step: make sector detail as reliable as sector list.

Recommended order:

1. Fix or add fallback for sector constituent fetch.
2. Return accurate sector data-source metadata.
3. Add sector detail empty-state UI.
4. Add tests for fallback source labeling and empty constituents.
5. Then continue toward sector money-flow history or rankings.
