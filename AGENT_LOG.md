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
- Desktop packaging: Tauri or Electron after the local web app MVP is stable.

The recommended development path is:

1. Build and stabilize a local web app.
2. Implement K-line, watchlist, price-position, and money-flow MVP features.
3. Add sectors, rankings, and daily review workflows.
4. Package the stable local app as a private desktop application.

## Current Repository Progress

- GitHub repo: `https://github.com/spreamming/VertTrade.git`
- Local branch: `main`
- Remote: `origin`
- Latest pushed commit on `main`: `agent log created`
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

Dependencies have not yet been installed, and runtime tests have not yet been run.

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
- Use commit identity `spreamming <fredspream@gmail.com>` for commits in this repo.
- Repo-local Git identity is already set: `user.name=spreamming`, `user.email=fredspream@gmail.com`.
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
