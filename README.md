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

This repository is at the project foundation stage. The first implementation target is:

1. Start a FastAPI backend.
2. Start a React frontend.
3. Connect the frontend to a backend health-check endpoint.
4. Fetch and store daily K-line data for one stock.
5. Render the first K-line and volume chart.

## Development Notes

Use a local SQLite database for MVP development. Keep external data-source adapters isolated from business logic so provider changes do not leak into the frontend or indicator calculations.

## Disclaimer

This project is for personal market analysis and learning. It does not provide investment advice, trading signals, or automated trading.
