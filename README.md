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

Stage 0 is complete. Phase 1 (basic market data and daily K-line MVP) is now implemented.

You can:

1. Search A-share stocks by code or name.
2. Open a stock detail page with latest quote summary.
3. View daily K-line and volume charts with zoom, pan, and crosshair.
4. Cache fetched K-line data in local SQLite.

Next target:

1. Watchlist management.
2. Dashboard with indices and watchlist summary.
3. Price-position / top-bottom zone indicator.

## Stage 0 Local Setup

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

The frontend reads `VITE_API_BASE_URL` when provided and otherwise uses `http://127.0.0.1:8000`.

Stage 0 is complete when:

- The backend starts and `/api/health` returns API and SQLite status.
- The frontend starts and displays the Stage 0 readiness card.
- The local SQLite database can be initialized under `data/market_watch.db`.

## Development Notes

Use a local SQLite database for MVP development. Keep external data-source adapters isolated from business logic so provider changes do not leak into the frontend or indicator calculations.

## Disclaimer

This project is for personal market analysis and learning. It does not provide investment advice, trading signals, or automated trading.
