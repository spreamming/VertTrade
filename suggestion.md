# Builder Suggestion

This file summarizes the latest checker process and gives focused suggestions for the next builder agent. It should be overwritten after every future checker run.

**Last checker run:** 2026-07-06 (eighth run)  
**Current stage checked:** Phase 7 ranking click-through workflow MVP  
**Source report:** `CHECKER_LOG.md`

---

## Checker Summary

The checker verified the current local stage: Phase 7 ranking click-through workflow.

Result: **PASS**.

Verified behavior:

- Backend tests pass: 38/38.
- Frontend typecheck passes.
- Frontend production build passes.
- `/api/rankings/daily-review?limit=5` returns 200.
- Live daily review returns all 8 ranking groups with items.
- Stock ranking rows are wired to open stock detail.
- Sector ranking rows are wired to open sector detail.
- Sector detail still supports constituent click-through to stock detail.
- Project remains a personal market observation app, not a trading platform.

---

## Builder Fix Suggestions

### 1. Add interaction coverage for ranking clicks

The click-through workflow compiles and is wired correctly, but there are no frontend interaction tests.

Suggested checks:

- A stock ranking row click opens `StockDetail`.
- A sector ranking row click opens `SectorDetail`.
- A constituent click inside `SectorDetail` opens `StockDetail`.
- Back from stock detail after opening from a sector returns to the sector detail.

If no frontend test framework is planned yet, do a short manual browser smoke test and record the result in `AGENT_LOG.md`.

### 2. Improve sector metadata when opened from rankings

Sector ranking rows carry only the fields available in `RankingItem`.

Current effect:

- Sector detail can fetch constituents with code/name.
- Some sector summary fields may show as `--` when opened from rankings.

Suggested improvement:

- If practical, enrich sector ranking items with more sector fields.
- Or let `SectorDetail` fetch sector summary data by code/name before rendering the header.
- Keep the page usable even when summary enrichment fails.

### 3. Make clickable ranking rows visually obvious

Ranking rows are now buttons. Make sure the UI clearly communicates they are clickable.

Suggested UI polish:

- Add hover/focus styling to `ranking-row-button`.
- Ensure keyboard focus state is visible.
- Consider a small text hint near the ranking panel: `点击条目查看详情`.

### 4. Keep navigation behavior intentional

Current state behavior is acceptable:

- Opening stock from Dashboard shows stock detail.
- Opening sector from Dashboard shows sector detail.
- Opening stock from sector detail shows stock detail.
- Back from that stock detail returns to the previous sector detail because selected sector remains in state.

If navigation grows further, consider making this explicit with a small navigation state helper instead of adding more independent selected-state branches.

### 5. Preserve ranking failure isolation

Do not regress the Phase 6 behavior:

- One failed ranking source should only affect its own group.
- Keep group-level error messages.
- Keep the available-group count note.
- Keep daily review usable even if one source is unavailable.

### 6. Keep wording observational

Continue using:

- 每日复盘
- 排行榜
- 查看详情
- 市场强弱
- 资金方向
- 观察维度

Avoid:

- 买入
- 卖出
- 建仓
- 清仓
- 交易信号

Rankings and click-through should support review, not trading instructions.

---

## Suggested Next Build Direction

Best next technical step: verify and polish the click-through workflow before adding more market data.

Recommended order:

1. Manually test ranking row click-through in the browser or add frontend interaction tests.
2. Add visible hover/focus states and a short click hint for ranking rows.
3. Improve sector summary data when opening sector detail from a ranking row.
4. Keep the daily review ranking error isolation intact.
5. Then move toward broader review workflow polish or realtime watch features.
