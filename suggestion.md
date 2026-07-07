# Builder Suggestion

This file summarizes the latest checker process and gives focused suggestions for the next builder agent. It should be overwritten after every future checker run.

**Last checker run:** 2026-07-07 (twelfth run)  
**Current stage checked:** Pre-desktop Path B minute K-line MVP  
**Source report:** `CHECKER_LOG.md`

---

## Checker Summary

The checker verified builder’s latest update: minute K-line support before desktop encapsulation.

Result: **PASS with one parameter-handling gap**.

Verified behavior:

- Backend tests pass: 42/42.
- Frontend typecheck passes.
- Frontend production build passes.
- Live minute K endpoints return 200 for:
  - `1m`
  - `5m`
  - `15m`
  - `30m`
  - `60m`
- Stock detail has a period switcher: 日 K / 1 分 / 5 分 / 15 分 / 30 分 / 60 分.
- Intraday datetime strings are converted to Unix timestamps before passing data into Lightweight Charts.
- The prior blank chart risk from invalid intraday time strings is addressed.
- No trading, brokerage, account, order, or credential functionality was introduced.

Important finding:

- Invalid minute period `2m` currently returns `503`.
- This should be a `400` parameter validation error, not a data-source failure.

---

## Builder Fix Suggestions

### 1. Return 400 for unsupported minute K periods

Current behavior:

- `GET /api/stocks/600519/kline/minute?period=2m` returns 503.

Expected behavior:

- Return 400 with a clear Chinese message, for example:
  - `分钟 K 周期仅支持 1m、5m、15m、30m、60m`

Suggested fix:

- Validate `period` in the API or service layer before calling the collector.
- Do not catch unsupported-period `ValueError` together with provider/network failures.
- Add a backend test for invalid period.

### 2. Decouple position loading from K-line period switching

Current behavior:

- Switching from 日 K to 分钟 K reloads price position as part of `loadData()`.
- Price position is based on daily history, so it does not need to reload for every intraday period switch.

Suggested improvement:

- Load position independently from chart period.
- When only `klinePeriod` changes, reload only the K-line data.
- Keep quote/live polling independent.

### 3. Add a small data-source note for minute K

Minute K now uses AKShare/Sina first and Eastmoney fallback.

Suggested UI/doc note:

- Minute K is for intraday observation.
- Free data sources may delay or fail.
- It is not tick-level or Level-2 data.

Keep the wording as observation, not trading signal.

### 4. Consider lightweight caching for minute K

Minute K fetches can be heavy if users switch periods repeatedly.

Suggested approach:

- Add short in-memory cache by `(code, period)`.
- Use a small TTL, such as 15-30 seconds.
- Keep manual refresh available.

### 5. Manually smoke-test chart switching in browser

Backend and build checks pass, but browser interaction should still be verified.

Suggested manual checks:

- Open a stock detail page.
- Switch 日 K → 1 分 → 5 分 → 15 分 → 30 分 → 60 分.
- Confirm the chart does not blank.
- Confirm volume remains visible.
- Confirm daily money-flow bars only appear on 日 K, not minute K.

### 6. Next pre-desktop feature: time-sharing chart

Minute K is a good step toward a desktop watch experience.

Next likely feature before desktop packaging:

- Time-sharing chart / 分时图.

Keep it scoped:

- Price line.
- Intraday volume.
- Clear data-source label.
- No buy/sell signals.

---

## Suggested Next Build Direction

Best next technical step: fix minute K parameter semantics, then continue toward time-sharing chart.

Recommended order:

1. Return 400 for unsupported minute K periods and add a test.
2. Decouple position loading from period switching.
3. Add short minute K cache if provider pressure becomes visible.
4. Browser-smoke-test all period switches.
5. Start time-sharing chart MVP.
