# VertTrade

VertTrade is a personal A-share market watch and analysis platform. It is designed for private use only: market observation, K-line review, price-position analysis, watchlists, sector analysis, and money-flow review.

It is not a trading platform. It does not connect to brokerage accounts, place orders, store securities credentials, or provide commercial market-data services.

## Project Goals

- View A-share indices, sectors, and individual stocks.
- Display K-line charts, volume, and basic market data.
- Calculate price-position and top/bottom risk zones.
- Track main money inflow/outflow where data is available.
- Manage a personal watchlist.
- Start as a local web app and later package as a private desktop app.

## Planned Stack

- Backend: Python, FastAPI, Pandas, SQLite
- Frontend: React, TypeScript, Vite
- Charts: TradingView Lightweight Charts and/or ECharts
- Data sources: AKShare first, with pytdx/Tushare as possible supplements
- Desktop packaging: Tauri or Electron after the core app is stable

## Repository Layout

```text
VertTrade/
  backend/
    app/
      main.py
      config.py
      database.py
    tests/
  frontend/
    src/
      api/
      components/
      pages/
      types/
      utils/
  data/
  docs/
  market_watch_requirements.md
  market_watch_development_plan.md
```

## Current Stage

Stage 0, Phase 1, and Phase 2 are complete. Phase 3 (price-position / top-bottom zone MVP) is now implemented.

You can:

1. Search A-share stocks by code or name.
2. Open a stock detail page with latest quote summary.
3. View daily K-line and volume charts with zoom, pan, and crosshair.
4. Cache fetched K-line data in local SQLite.
5. Add searched stocks to a local watchlist.
6. View and delete watchlist items from the Dashboard.
7. Open stock detail pages directly from the watchlist.
8. View a 0-100 price-position score and top/bottom zone label on stock detail pages.
9. See the current price-position label in the watchlist table.

Next target:

1. Main money-flow MVP.
2. Major index and market overview data for the Dashboard.
3. Broader price-position support for indices and additional windows in the UI.

## Local Setup

Create and activate a Python virtual environment, then install backend dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the backend from the repository root:

```bash
uvicorn backend.app.main:app --reload
```

The backend health endpoint is available at:

```text
http://127.0.0.1:8000/api/health
```

Install and start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`. `VITE_API_BASE_URL` can still be provided for non-dev deployments.

## Current App Flow

1. Open `http://127.0.0.1:5173`.
2. Search by A-share code or name.
3. Add search results to the local watchlist from the Dashboard.
4. Open a stock detail page from either search results or the watchlist.
5. Review latest quote summary, daily K-line, and volume.
6. Delete stocks from the watchlist when no longer needed.

The Dashboard currently focuses on the watchlist MVP. Major indices, market breadth, turnover, and richer market overview data are planned later.

## Verification

Run backend tests from the repository root:

```bash
.venv/bin/python -m pytest backend/tests
```

Run frontend checks:

```bash
cd frontend
npm run typecheck
npm run build
```

## Development Notes

Use a local SQLite database for MVP development. Keep external data-source adapters isolated from business logic so provider changes do not leak into the frontend or indicator calculations.

## Disclaimer

This project is for personal market analysis and learning. It does not provide investment advice, trading signals, or automated trading.
