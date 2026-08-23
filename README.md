# FuturesPulse

Wyckoff Day Trading Timing Model for futures. Static browser app on GitHub Pages, GitHub Actions
for ingestion, this repo as both datastore and source of truth.

**Resume in any Claude session: say `load futurespulse`.**

    .fp-config.json                  canonical file list + load instruction — READ FIRST
    master-spec.md                   the decoded model
    session-state/
      latest-resume-note.md          where we are — the single source of truth on state
      DECISIONS.md                   why things are the way they are
      PROJECT-CONSTANTS.md           values that must not drift
    changelog/CHANGELOG.md
    engine/zigzag.js                 ZigZag, wave table, BW/BV, Biggest Wave/Volume In
    pipeline/ingest.py               Yahoo → 1m → resample 3m → append
    .github/workflows/ingest.yml     daily cron, commits the data back
    current/index.html               THE APP — not built yet
    data/ES/{YYYY-MM}.json           3m bars, columnar

## Why the data lives in the repo

Yahoo blocks cross-origin browser requests, so the page cannot fetch it. The Action runs Python
where that restriction does not apply, commits the result, and Pages serves app and data from the
same origin — so the browser fetch is same-origin and CORS never arises.

Ingestion stays deliberately dumb: fetch, dedupe, append, commit. All analysis runs client-side, so
the model can be iterated without touching the pipeline or waiting for a deploy.

## The constraint that sets the cadence

| Interval | Yahoo window |
|---|---|
| `1m` | **~7 days** |
| `2m` `5m` `15m` `30m` `60m` `90m` | 60 days |
| `3m` | **does not exist** |

3m must be resampled from 1m — 2m does not divide into 3m — and 1m expires after a week.
**A gap longer than seven days is permanent.** `ingest.py` exits non-zero on any symbol failure
rather than logging and carrying on.

## Setup

    git init && git add . && git commit -m "init"
    gh repo create futurespulse --public --source=. --push

Then: **Settings → Pages → Deploy from a branch → `main` / root**, and
**Settings → Actions → General → Workflow permissions → Read and write**.

    pip install -r pipeline/requirements.txt
    python pipeline/ingest.py --symbols ES --dry-run

Then run the workflow by hand once — **Actions → Ingest market data → Run workflow** — and read the
log. That run is the first real proof the Yahoo path works end to end.

## Wave engine

Verified against the original app on ES 2026-08-21: 24/24 pivots, the 22.50 pt Dmd wave, its 1.633
extension, and the 24.50 pt / 27 min target wave.

    Swing HIGH at bar i  ⟺  High[i] ≥ High[j] for all j ∈ [i−3, i+3], j ≠ i
    Swing LOW  at bar i  ⟺  Low[i]  ≤ Low[j]  for all j ∈ [i−3, i+3], j ≠ i

Highs and lows tested independently and merged chronologically; consecutive same-type candidates
collapse to the more extreme one; exact ties keep the earlier bar; no minimum-move filter. Pass
`requireConfirmation: true` for real-time use — a pivot needs 3 bars after it, so live detection
runs 9 minutes behind.
