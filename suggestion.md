# Builder Suggestion

This file summarizes the latest checker process and gives focused suggestions for the next builder agent. It should be overwritten after every future checker run.

**Last checker run:** 2026-07-03 (seventh run)  
**Current stage checked:** Phase 6 daily review / ranking MVP  
**Source report:** `CHECKER_LOG.md`

---

## Checker Summary

The checker verified the current local stage: Phase 6 daily review / rankings.

Result: **PASS**.

Verified behavior:

- Backend tests pass: 37/37.
- Frontend typecheck passes.
- Frontend production build passes.
- `/api/rankings/daily-review?limit=5` returns 200.
- Live daily review returns all 8 ranking groups.
- Each ranking group has live items and no error in the smoke check.
- Dashboard shows the daily review / ranking panel.
- Per-group source labels and error/empty states are implemented.
- Project remains a personal market observation app, not a trading platform.

Live ranking groups verified:

- 个股涨幅榜
- 个股跌幅榜
- 成交额榜
- 换手率榜
- 个股主力净流入榜
- 个股主力净流出榜
- 板块涨幅榜
- 板块资金流榜

---

## Builder Fix Suggestions

### 1. Keep provider failure isolation

The current design is good: a single failed ranking source should only affect its own group.

Preserve this behavior when modifying ranking code:

- Do not let one failed stock source break sector rankings.
- Do not let one failed money-flow source break price/amount/turnover rankings.
- Keep group-level Chinese error messages.
- Keep the summary note showing how many ranking groups are available.

### 2. Format `ranking_service.py`

`backend/app/services/ranking_service.py` runs correctly, but the sector group construction has awkward indentation.

Suggested fix:

- Run a formatting pass or manually align the list entries.
- Keep the logic unchanged unless tests require a behavior change.
- Add or keep tests around all 8 ranking groups after formatting.

### 3. Consider lightweight daily-review caching

Live ranking data depends on external providers. The latest smoke test passed, but provider stability has been a recurring issue.

Suggested approach:

- Add a short-lived cache for the daily review response.
- Keep the last successful response visible if refresh fails.
- Make cache age visible in the UI later if needed.
- Do not add historical ranking storage yet unless the user asks for daily snapshots.

### 4. Improve Dashboard usability before adding more panels

Dashboard now includes:

- Add watchlist
- Watchlist table
- Daily review / rankings
- Industry sector table
- Market notes

Suggested UI direction:

- Keep section ordering clear: watchlist first, daily review second, sectors third.
- Consider collapsible sections or tabs later if the page becomes too long.
- Avoid adding more large panels until the current Dashboard remains easy to scan.

### 5. Consider click-through from rankings later

Ranking cards are currently read-only.

Possible enhancement:

- Stock ranking items could open `StockDetail`.
- Sector ranking items could open `SectorDetail`.

This is useful, but not required to accept the current Phase 6 MVP.

### 6. Keep wording observational

Continue using:

- 每日复盘
- 排行榜
- 市场强弱
- 资金方向
- 观察维度

Avoid:

- 买入
- 卖出
- 建仓
- 清仓
- 交易信号

Rankings should support market review, not trading instructions.

---

## Suggested Next Build Direction

Best next technical step: stabilize and polish the daily review experience before expanding into new stages.

Recommended order:

1. Format and simplify `ranking_service.py`.
2. Add lightweight daily-review response caching.
3. Keep last successful ranking data visible on refresh failure.
4. Consider click-through from ranking rows to stock/sector detail.
5. Then move toward broader review workflow or realtime watch features.
