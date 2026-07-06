# Builder Suggestion

This file summarizes the latest checker process and gives focused suggestions for the next builder agent. It should be overwritten after every future checker run.

**Last checker run:** 2026-07-06 (tenth run)  
**Current stage checked:** Stage 9 stability / data quality / desktop packaging concept MVP  
**Source report:** `CHECKER_LOG.md`

---

## Checker Summary

The checker verified whether current work follows the plan through Stage 9 and whether previous stages meet their acceptance expectations.

Result: **PASS**.

Verified behavior:

- Backend tests pass: 40/40.
- Frontend typecheck passes.
- Frontend production build passes.
- Live quotes for `600519` and `000001` return 200.
- Live quote responses include `is_stale` and `cache_age_seconds`.
- Daily review endpoint returns 8 populated ranking groups.
- Stage 9 stale realtime quote fallback test exists.
- Stage 9 stability / data quality / desktop packaging concept doc exists.
- Stage 0 through Stage 8 remain aligned with the planned build order.
- Project remains a personal market observation app, not a trading platform.

Overall assessment:

- Stage 9 is acceptable as a **documentation + test MVP**.
- It is not yet an executable desktop packaging proof of concept.

---

## Builder Fix Suggestions

### 1. Turn Stage 9 desktop concept into a runnable local launcher

Current Stage 9 documentation is useful, but still conceptual.

Suggested next step:

- Add a local launcher script that starts backend and frontend in the correct order.
- Check whether ports `8000` and `5173` are already occupied.
- Print clear Chinese startup instructions and URLs.
- Keep this as a local developer/private-user launcher before choosing Electron or Tauri.

### 2. Normalize Stage / Phase naming

The project currently uses both `Phase` and `Stage`.

Suggested cleanup:

- Use one naming convention in docs going forward.
- If keeping both, define the mapping clearly once.
- Keep historical log entries unchanged unless they are confusing.

### 3. Improve README current flow

`README.md` now points to Stage 9 docs, but the app has grown beyond the old short flow.

Suggested README structure:

- Core stock flow: search, K-line, price position, money-flow.
- Watchlist flow: add/delete, live refresh, review summary.
- Dashboard flow: daily review rankings and sectors.
- Realtime flow: near-realtime quote polling and staleness labels.
- Stability / desktop preparation: Stage 9 docs.

### 4. Add browser smoke verification for realtime behavior

Backend tests cover stale fallback, but browser behavior still needs manual or automated verification.

Suggested checks:

- Stock detail quote updates without full page reload.
- Watchlist quote and change-percent update after polling.
- Cached/stale quote status is visible when applicable.
- Historical K-line, position, and money-flow panels remain usable if live quote refresh fails.

### 5. Keep Stage 9 scope focused

Stage 9 should harden the local MVP before adding more features.

Good Stage 9 work:

- Better startup scripts.
- Data quality docs.
- Cache/staleness tests.
- Provider fallback tests.
- Desktop shell concept proof.

Defer:

- AI analysis.
- News.
- Backtesting.
- Complex alerts.
- Brokerage or trading integrations.

### 6. Preserve no-trading wording

Continue using:

- 近实时
- 行情观察
- 数据质量
- 缓存回退
- 本地桌面壳

Avoid:

- 买入
- 卖出
- 建仓
- 清仓
- 交易信号
- 下单

Stage 9 should improve reliability and packaging readiness, not move toward trading execution.

---

## Suggested Next Build Direction

Best next technical step: make Stage 9 operational instead of only conceptual.

Recommended order:

1. Add a local launcher script for backend + frontend.
2. Add startup checks for ports and dependency presence.
3. Update README with grouped current app flows.
4. Add browser smoke notes or lightweight frontend interaction tests for realtime polling.
5. Re-evaluate Electron vs Tauri only after the launcher path works smoothly.
