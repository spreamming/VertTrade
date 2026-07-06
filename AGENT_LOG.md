# VertTrade Agent Log

This file is the shared project memory for agents working on VertTrade. Read it before making changes, and update it after each meaningful step so future agents understand the current context, progress, and rules.

## Current Project Context

VertTrade is a personal A-share market watch and analysis platform. It is for private use only, not business use.

The project goal is to build a desktop application that helps with:

- A-share market observation and daily review.
- K-line, volume, and basic quote display.
- Price position / top-bottom risk zone analysis.
- Main money inflow/outflow analysis.
- Watchlist management.
- Sector and ranking review.

The project must not become a trading platform. It must not support brokerage login, order placement, automatic trading, account credential storage, or commercial data redistribution.

## Current Technical Direction

The planned architecture is local-app first:

- Backend: Python, FastAPI, Pandas, SQLite.
- Frontend: React, TypeScript, Vite.
- Charts: TradingView Lightweight Charts and/or ECharts.
- Data sources: AKShare first, with pytdx/Tushare as possible supplements.
- Real-time market watch: planned as a later stage after core analysis features, starting with 1-3 second quote refresh, intraday K-line, time-sharing chart, and watchlist fast refresh. True tick/Level-2 data is a later evaluation item and may require paid/professional data sources.
- Desktop packaging: Tauri or Electron after the local web app MVP is stable.

The recommended development path is:

1. Build and stabilize a local web app.
2. Implement K-line, watchlist, price-position, and money-flow MVP features.
3. Add sectors, rankings, and daily review workflows.
4. Add near real-time market watch features: live quotes, intraday K-line, time-sharing chart, and watchlist fast refresh.
5. Package the stable local app as a private desktop application.

## Git Commit Policy (IMPORTANT)

> **Only `spreamming <fredspream@gmail.com>` may appear as a contributor.**
>
> Never add `Co-authored-by: Cursor <cursoragent@cursor.com>` or any other assistant co-author trailer. GitHub treats those trailers as real contributors even when author/committer are correct.
>
> Before every commit and push, verify with:
>
> `git log -1 --format='%an <%ae>%n%cn <%ce>%n%B'`
>
> If a co-author trailer appears, recreate the commit without it before pushing. See `.cursor/rules/Git-Rules.mdc` for the safe `git commit-tree` pattern.

Older pushed commits before `dd0b997` may still contain Cursor co-author trailers in history. New commits must not repeat that mistake.

## Current Repository Progress

- GitHub repo: `https://github.com/spreamming/VertTrade.git`
- Local branch: `main`
- Remote: `origin`
- Latest pushed commit on `main`: `d679ed8 stage 7`
- Correct Git identity for commits: `spreamming <fredspream@gmail.com>`
- Repo-local Git identity is configured in `.git/config` so future commits in this repo use the correct author.

Initial scaffold already created:

- `README.md`
- `.gitignore`
- `.editorconfig`
- `.env.example`
- `requirements.txt`
- `backend/app/main.py` with `/api/health`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/tests/test_health.py`
- `frontend/` React + Vite + TypeScript starter
- `frontend/src/api/client.ts`
- `frontend/src/App.tsx`
- `data/`
- `docs/`
- `market_watch_requirements.md`
- `market_watch_development_plan.md`

Dependencies have been installed locally.

Stage 0 through Phase 7 are complete and pushed. Stage 8 realtime market watch MVP is ready to commit as stage 8.

Current verification commands have passed:

- `.venv/bin/python -m pytest backend/tests`
- `npm run typecheck`
- `npm run build`

## Agent Rules For This Project

- Read this `AGENT_LOG.md` before starting substantial work.
- Update this file after each meaningful step or completed task.
- Keep updates factual and concise: what changed, why, and any important verification result.
- Preserve the project boundary: personal market analysis only, no trading functionality.
- Do not add brokerage login, order placement, automatic trading, or credential storage.
- Use the existing planned stack unless the user approves a change.
- Keep MVP scope focused: K-line, volume, search, watchlist, price position, top/bottom zone, and money flow first.
- Delay AI, news, finance, backtesting, complex alerts, and desktop packaging until the core workflow is stable.
- Do not change global Git configuration unless the user explicitly asks.
- **Git commits must never include Cursor or any assistant as co-author.** Only `spreamming <fredspream@gmail.com>` is allowed on GitHub contributor history for new work.
- Use commit identity `spreamming <fredspream@gmail.com>` for commits in this repo.
- Repo-local Git identity is already set: `user.name=spreamming`, `user.email=fredspream@gmail.com`.
- Before commit/push, verify the latest commit body has no `Co-authored-by:` trailer.
- Do not create commits or push unless the user explicitly asks.
- Be careful with user changes in the working tree; do not revert unrelated edits unless asked.
- User terminal preference to preserve: Windows 11 / PowerShell style, use `py` for Python files, and avoid command chaining with `&&`.

## Progress Log

### 2026-07-02

- Created initial project roadmap from `market_watch_requirements.md` and `market_watch_development_plan.md`.
- Created standard project scaffold for backend, frontend, data, docs, and repository hygiene files.
- Initialized Git repository and pushed initial scaffold to GitHub.
- Corrected the pushed initial commit author/committer to `spreamming <fredspream@gmail.com>`.

### 2026-07-03

- Created this root-level `AGENT_LOG.md` as the shared agent memory and project activity log.
- Fixed the `agent log created` commit author after it was pushed with the auto-detected local identity.
- Set repo-local Git identity so future commits in this repository default to `spreamming <fredspream@gmail.com>`.
- Started Stage 0 foundation build: backend health now checks SQLite readiness, frontend displays API/database readiness, planned backend/frontend module directories were created, and README startup instructions were added.
- Completed Stage 0 verification: installed backend/frontend dependencies, backend tests pass, frontend typecheck passes, frontend production build passes, and `GET /api/health` returned API/database `ok`.
- Implemented Phase 1 MVP: stock search, daily K-line fetch/cache via AKShare, quote summary API, SQLite models for stocks and daily K-lines, frontend search box, stock detail page, and Lightweight Charts K-line/volume panel.
- Verified Phase 1 live flow: search for `600519` returns 贵州茅台, K-line API returns cached daily bars, backend tests (4) pass, frontend typecheck/build pass.
- Fixed stock detail "Failed to fetch": AKShare requests now bypass broken system proxy settings, backend returns clear 503 errors instead of crashing, frontend uses one K-line request (quote derived locally), Vite dev proxy added for `/api`, and error messages improved.
- Updated frontend language requirement: all user-visible frontend text should be Simplified Chinese. Converted current frontend labels, buttons, placeholders, loading text, chart titles, and displayed error messages to Chinese; added the language rule to `market_watch_development_plan.md`.
- Updated the project roadmap to include a later real-time market watch stage: near real-time quotes, intraday K-line, time-sharing chart, WebSocket/SSE-style frontend updates, watchlist fast refresh, and clear scope boundaries that this is still a personal analysis app rather than a trading terminal.
- Implemented Phase 2 MVP: local watchlist model/repository/API, Dashboard API, Chinese Dashboard page, watchlist add/delete flow, watchlist table with quote summary, and navigation from watchlist to stock detail. Major index and market breadth data remain planned for later Dashboard expansion.
- Added root-level `suggestion.md` as the overwrite-style builder guidance file that summarizes the latest checker run and recommended fixes after each check process.
- Applied `suggestion.md` follow-up fixes for Phase 2: refreshed stale `AGENT_LOG.md` repository metadata, documented current app flow and verification commands in `README.md`, added `pytest.ini` for stable repo-root test discovery, and re-ran backend tests plus frontend typecheck/build successfully.
- Committed and pushed `dd0b997 stage 2` without any `Co-authored-by` trailer after user reported Cursor Agent appearing on GitHub from earlier co-author lines.
- Highlighted permanent Git policy in `AGENT_LOG.md`, `.cursor/rules/Git-Rules.mdc`, and `market_watch_development_plan.md`: only `spreamming <fredspream@gmail.com>` may appear as contributor; never add Cursor co-author trailers on new commits.
- Implemented Phase 3 MVP: backend price-position indicator based on rolling high/low range, `/api/stocks/{code}/position`, 250/750/1250-day backend windows, Chinese top/bottom zone labels, stock detail position card, and watchlist position labels. Verified backend tests, frontend typecheck, and frontend build.
- Applied `suggestion.md` Phase 3 follow-ups: tightened K-line cache end-date freshness (4-day calendar tolerance for weekends/holidays), refactored quote + position to reuse one K-line lookup via `get_quote_and_position`, and added direct `position_score` boundary unit tests (24 backend tests pass).
- Committed and pushed `d9a3c3d stage 3` without any `Co-authored-by` trailer (recreated via `commit-tree` after Cursor injected co-author on first attempt).
- Implemented Phase 4 MVP: AKShare individual stock main money-flow collector, SQLite `moneyflow_daily` cache, `/api/stocks/{code}/moneyflow`, stock detail money-flow summary + bar chart, and watchlist main net inflow columns. Verified 26 backend tests, frontend typecheck, and frontend build.
- Added `.cursor/rules/stage-frontend-changelog.mdc`: after each completed stage, agent must explain new frontend UI/features vs the previous stage in Simplified Chinese.
- Adjusted Phase 4 frontend chart layout: main money-flow bars now render inside the K-line chart under volume on the same time axis; the standalone money-flow chart panel was removed. Frontend typecheck/build pass.
- Applied Phase 4 checker suggestions: stock detail now loads core quote/K-line/position separately from optional money-flow, so money-flow failures show a local warning instead of blocking the page; money-flow collector validates required AKShare columns; proxy bypass was strengthened for requests; backend tests now 27 pass and frontend typecheck/build pass. Live money-flow check: `000001` SZ succeeds, `600519` SH still returns an upstream connection close handled by the API.
- Localized K-line chart date labels: the bottom time axis and crosshair date formatter now display Chinese date text. Frontend typecheck/build pass.
- Implemented Phase 5 industry sector MVP: added AKShare industry sector collector with field validation, `/api/sectors/industries`, `/api/sectors/industries/{code}`, Dashboard industry sector table, sector detail page with constituents, and click-through from constituents to stock detail. Backend tests now 30 pass; frontend typecheck/build pass. Live sector data source currently returns upstream connection close and is handled by API as a Chinese 503 error.
- Fixed industry sector data-source availability: added 同花顺 sector summary fallback when 东方财富 industry list fails, mapped fallback amount/main-net-inflow fields, and changed sector constituent lookup to prefer sector name over provider-specific code. Live `/api/sectors/industries` now returns 200 with 90 sectors; backend tests now 31 pass and frontend typecheck/build pass.
- Applied Phase 5 checker suggestions: sector list/detail responses now carry accurate `source` metadata, sector detail tries name/code and has a 同花顺 constituent fallback, and the frontend shows source labels plus an empty constituent state. Live sector detail smoke test now returns 200 with constituents; backend tests now 33 pass and frontend typecheck/build pass.
- Committed and pushed `5974030 stage 5` without any `Co-authored-by` trailer (recreated via `commit-tree` after Cursor injected co-author on first attempt). Verified 33 backend tests, frontend typecheck, and push to `origin/main`.
- Implemented Phase 6 MVP: added `/api/rankings/daily-review`, ranking schemas/service/collector with per-group fallback handling, Dashboard daily review/ranking panel, sector gainers and sector money-flow rankings from 同花顺 industry summary. Backend tests now 35 pass; frontend typecheck/build pass. Live daily review returns 200 with sector ranking groups; all-market stock ranking sources remain unstable and are hidden by default unless `include_stock=true`.
- Cleaned Phase 6 default Dashboard UX: default daily review now returns only `sector_gainers` and `sector_moneyflow`, so six unstable all-market stock ranking error cards no longer appear. Backend tests now 36 pass; frontend typecheck/build pass.
- Reworked Phase 6 ranking stability after user feedback: default daily review again includes all 8 ranking groups. Stock行情榜 now uses lightweight direct Eastmoney top-list requests with Tonghuashun page fallback; stock money-flow rankings use Eastmoney direct flow lists with Tonghuashun flow fallback. Live smoke now returns items for all stock, money-flow, and sector ranking groups; backend tests now 37 pass and frontend typecheck/build pass.
- Applied Phase 6 checker suggestions: formatted/simplified `ranking_service.py`, added a 60-second daily-review response cache that only stores fully populated responses, and keeps source failures isolated per ranking group. Live smoke returns 8/8 groups with data and second request hits cache; backend tests now 38 pass and frontend typecheck/build pass.
- Committed and pushed `2042be7 stage 6` without any `Co-authored-by` trailer (recreated via `commit-tree` after Cursor injected co-author on first attempt). Verified 38 backend tests, frontend typecheck, and push to `origin/main`.

### 2026-07-06

- Implemented Phase 7 MVP: daily review ranking rows are now clickable. Stock ranking rows open `StockDetail`; sector ranking rows open `SectorDetail`; sector detail still supports constituent click-through to stock detail. Verified 38 backend tests and frontend typecheck/build.
- Applied Phase 7 checker suggestions: ranking rows now show clearer click affordance and keyboard focus styling, the ranking panel includes a “点击条目可查看详情” hint, and sector ranking click-through carries additional sector summary metadata into `SectorDetail`. Verified 38 backend tests and frontend typecheck/build.
- Committed and pushed `d679ed8 stage 7` without any `Co-authored-by` trailer (recreated via `commit-tree` after Cursor injected co-author on first attempt). Verified 38 backend tests, frontend typecheck, and push to `origin/main`.
- Re-checked the roadmap before Stage 8 and found one unfinished Stage 7 item: watchlist review summary. Reverted the mistaken local "Phase 8 sector money-flow snapshot" work, added a Dashboard watchlist review summary for high/low price position, money-flow counts, strongest/weakest watchlist names, and verified 38 backend tests plus frontend typecheck/build. The next correct stage remains Stage 8 real-time market watch.
- Implemented Stage 8 realtime market watch MVP: added Eastmoney live quote collector with 3-second in-memory cache, `/api/stocks/{code}/quote/live`, stock detail 3-second live quote polling, and watchlist lightweight live price refresh every 5 seconds. Live smoke returned realtime quotes for `600519` and `000001`; backend tests now 39 pass and frontend typecheck/build pass. Minute K/time-sharing chart remains future work.
- Fixed Stage 8 Dashboard realtime behavior: watchlist live refresh now merges the full live quote payload, so latest price, change amount/percent, trade date, and watchlist review summary all update from realtime data rather than only replacing the latest price. Verified 39 backend tests and frontend typecheck/build.
- Improved Stage 8 quote freshness accuracy: live quote collector now prefers Tencent quote data with provider quote time and uses Eastmoney as fallback; UI displays both provider quote time and local refresh time, uses “近实时” wording, and polling requests `refresh=true` to avoid confusing backend cache with source freshness. Verified 39 backend tests and frontend typecheck/build.
- Applied Stage 8 checker suggestions: live quote responses now include `is_stale` and `cache_age_seconds`; UI distinguishes “近实时” from “缓存行情”; Dashboard caps automatic watchlist live refresh to the first 20 rows and merges full live quote fields into the table and watchlist review summary. Updated README/plan wording to Tencent-first with Eastmoney fallback. Verified backend tests and frontend typecheck/build.
