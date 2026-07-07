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

Stage 0 through Stage 8 are complete. Stage 9 (stability, data quality, and desktop packaging concept) is now implemented locally.

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
10. View daily main money inflow/outflow bars and summary on stock detail pages.
11. See latest main net inflow and ratio in the watchlist table.
12. View industry sector summaries on the Dashboard.
13. Open an industry sector detail page and inspect constituent stocks.
14. Jump from a sector constituent directly into the stock detail page.
15. View a daily review panel with stock and sector rankings.
16. Review stock and sector rankings with a consistent Tonghuashun ranking source.
17. Click stock ranking rows to open stock detail pages.
18. Click sector ranking rows to open sector detail pages.
19. Review a watchlist summary with high/low position counts, money-flow counts, and strongest/weakest watchlist names.
20. Use near-real-time quote refresh on stock detail pages.
21. See lightweight near-real-time price and change-percent refresh in the watchlist table, including provider quote time and local refresh time.
22. Review Stage 9 stability and desktop packaging notes in `docs/stage9_stability_desktop_packaging.md`.
23. Switch stock detail charts between daily K and 1 / 5 / 15 / 30 / 60 minute K.
24. View a time-sharing chart with price line, average-price line, and intraday volume.

Next target:

1. Prototype desktop shell startup around the local backend/frontend.
2. Major index and market overview data for the Dashboard.
3. Add richer intraday chart polish if needed.

## Local Setup

Create and activate a Python virtual environment, then install backend dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the local app with the launcher:

```bash
.venv/bin/python scripts/start_local.py
```

The launcher checks ports `8000` and `5173`, starts missing services, and prints the local URLs.

Or start the backend manually from the repository root:

```bash
uvicorn backend.app.main:app --reload
```

The backend health endpoint is available at:

```text
http://127.0.0.1:8000/api/health
```

Install and start the frontend manually:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`. `VITE_API_BASE_URL` can still be provided for non-dev deployments.

## Current App Flow

Open `http://127.0.0.1:5173`.

Core stock flow:

1. Search by A-share code or name.
2. Open a stock detail page.
3. Review near-realtime quote, daily K-line, price position, and money-flow bars.

Watchlist flow:

1. Add or delete local watchlist items from the Dashboard.
2. Watchlist prices and change-percent fields refresh with near-realtime quotes.
3. Review the watchlist summary for high/low position and money-flow focus.

Dashboard flow:

1. Review daily ranking cards for stock and sector strength.
2. Click ranking rows into stock or sector detail pages.
3. Review industry sectors and open sector constituents.

Realtime flow:

1. Stock detail polls near-realtime quotes every 3 seconds.
2. Watchlist refreshes the first 20 rows every 5 seconds.
3. Quote time, refresh time, stale/cache status are displayed so provider freshness is visible.

Stability / desktop preparation:

- See `docs/stage9_stability_desktop_packaging.md`.

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
