# Builder Suggestion

This file summarizes the latest checker process and gives focused suggestions for the next builder agent. It should be overwritten after every future checker run.

**Last checker run:** 2026-07-03 (third run)  
**Scope checked:** Stage 0 + Phase 1 on remote, Phase 2 watchlist MVP in local working tree  
**Source report:** `CHECKER_LOG.md`

---

## Checker Summary

The checker verified that Stage 0 and Phase 1 are already committed and pushed. The latest remote commit is `7ca4d43 stage 1`.

The current local work implements a Phase 2 watchlist and Dashboard MVP. It adds watchlist CRUD, a Dashboard API, a Chinese Dashboard page, a watchlist table with quote summaries, and navigation from watchlist rows to the stock detail page.

Verification results from the checker:

- Backend tests pass: 8/8.
- Frontend typecheck passes.
- Frontend production build passes.
- Live watchlist API and Dashboard API checks pass.
- No brokerage login, order placement, auto-trading, or credential storage was introduced.

Overall verdict: **good, on plan, but uncommitted**.

---

## Main Problems To Fix

1. **Phase 2 work is not committed or pushed**
   - The watchlist/Dashboard MVP exists only in the local working tree.
   - Remote is still at `stage 1`.
   - Do not commit unless the user explicitly asks.

2. **`AGENT_LOG.md` top metadata is stale**
   - It still says latest pushed commit is `agent log created`.
   - It still says dependencies and runtime tests have not been run.
   - This contradicts the actual progress log and checker results.

3. **Phase 2 is only a watchlist MVP**
   - Watchlist CRUD and dashboard summary are done.
   - Major indices, market breadth, turnover, and richer market overview are still deferred.
   - Keep calling it "Phase 2 MVP" unless those deferred items are implemented.

4. **Test command is still not standardized**
   - Tests pass with `.venv/bin/python -m pytest backend/tests/`.
   - Consider adding `pytest.ini` or documenting this exact command in `README.md`.

5. **Minor cleanup remains**
   - `echarts` is listed as a frontend dependency but is not used yet.
   - Confirm `frontend/tsconfig.tsbuildinfo` is ignored and does not reappear as untracked.

---

## Suggested Builder Actions

### First priority

Update `AGENT_LOG.md` Current Repository Progress so it reflects reality:

- Latest pushed commit: `7ca4d43 stage 1`.
- Stage 0 and Phase 1 are complete and pushed.
- Phase 2 watchlist MVP is implemented locally and verified, but not pushed.
- Dependencies are installed.
- Backend tests and frontend build/typecheck have been run successfully.

### Second priority

Update `README.md` to describe the current app flow:

- Start backend and frontend.
- Search A-share stock code/name.
- Open stock detail with K-line and volume.
- Add/delete watchlist items from Dashboard.
- Explain that major indices and market overview are planned later.

### Third priority

Stabilize test/documentation workflow:

- Add a `pytest.ini` with repo-root import behavior, or document `.venv/bin/python -m pytest backend/tests/`.
- Keep frontend validation commands documented: `npx tsc --noEmit` and `npm run build`.

### Commit guidance

If the user asks to commit, stage the Phase 2 files and use a message like:

```text
stage 2 watchlist
```

Only commit and push after explicit user instruction.

---

## Next Development Direction

After Phase 2 watchlist MVP is committed, the next useful builder step is either:

- Complete the remaining Dashboard market overview items: major indices, market breadth, turnover, and market notes backed by data.
- Start Phase 3: price position / top-bottom zone indicator.

Do not start trading, brokerage, account, order, or credential features.
