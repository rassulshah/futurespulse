# RESUME NOTE — 2026-08-23 — scaffold + verified engine, no UI yet

## WHERE WE ARE IN ONE LINE

The original app has been decoded (sections 3–5), the ZigZag has been reverse-engineered and
**verified 24/24 against the live app**, the ingestion pipeline is written but **has never run**,
and 15 months of ES data is loaded. **No UI exists yet.**

## ⛔ STANDING RULE — DO NOT REPEAT THE ORIGINAL APP'S CENTRAL MISTAKE

The original app reported a weekday as **86% green** off **6 observations**. The full 15-month
sample says that weekday is **58.1% green over 62 sessions**, and its 95% confidence interval
spans 50%. **Every statistic this project displays must carry `n` and an interval.** A percentage
without a sample size is not a finding, it is a coin flip with a decimal point.

## ⚠ READ `session-state/DECISIONS.md` BEFORE PROPOSING ANY CHANGE TO SECTION 3

It records the measurement that killed the original directional premise, and why the range half of
Section 3 survives while the direction half does not.

## BUILD STATE

| Component | State | Verified? |
|---|---|---|
| `engine/zigzag.js` | **built** | **YES** — 24/24 pivots, extension 1.633, target wave 24.50/27m |
| `pipeline/ingest.py` | built | resample half proven; **Yahoo fetch NEVER RUN** |
| `.github/workflows/ingest.yml` | built | **never executed** |
| `data/ES/` | 153,959 3m bars, 17 months | round-trips correctly |
| `current/index.html` (the app) | **NOT BUILT** | — |
| Section 3 UI | not built | — |
| Sections 4 / 5 | **blocked** — see OPEN THREADS | — |

## LOCKED DECISIONS (user-confirmed)

- **Green / red day** = Close vs Open. Not close vs prior close.
- **Range** = session High − Low.
- **Predictor** = weekday. Single variable.
- **Verdict** = a count of prior same-weekday sessions.
- **HTF context badges** (`DC<PWC`, `DC>MO`, `WC>MO`) — **CUT**. Not in the rebuild.
- **Architecture** — GitHub repo as datastore + source of truth; GitHub Actions for ingestion;
  static browser app on GitHub Pages. **Public repo** (Pages on a private repo needs a paid plan).
- **Bars** = 3-minute. Not 5m, despite 5m having an easier Yahoo window.
- **ZigZag** = 3-bar high/low reversal, meaning **3 bars on EACH side**.
- **No Google Drive.** Unlike gex, there is no Drive mirror in this project.

## THE ZIGZAG RULE — VERIFIED, DO NOT RE-DERIVE

```
Swing HIGH at bar i  ⟺  High[i] ≥ High[j] for all j ∈ [i−3, i+3], j ≠ i
Swing LOW  at bar i  ⟺  Low[i]  ≤ Low[j]  for all j ∈ [i−3, i+3], j ≠ i
```

Window clamps at the array edges. Highs and lows are tested independently and merged
chronologically. Consecutive same-type candidates collapse to the more extreme one. **Exact ties
keep the EARLIER bar** — this single rule was the difference between 22/24 and 24/24. There is no
minimum-move filter: the smallest leg in the reference session is 3.50 pts over 4 bars, and two
legs are a single bar long.

k=1 and k=2 also pass for every pivot, but **k=4 fails at five of them** — so 3 is exactly right,
not "at least 3".

A pivot cannot be confirmed until 3 bars print after it, so live detection runs **9 minutes
behind** on 3m bars. `zigzag(bars, 3, {requireConfirmation:true})` for real-time use.

## DATA COVERAGE

```
ES   2025-03-30 → 2026-07-17     153,959 3m bars   17 monthly partitions   7.2 MB
     336 RTH sessions, 323 of them complete 390-bar days
     source: user's 1-minute export (460,784 bars), resampled
```

⚠ **PERMANENT GAP: 2026-07-17 → present, ~26 trading days.** Yahoo serves 1m for only 7 days, so
3m bars for that stretch can never be rebuilt. It affects Sections 4/5 only — Section 3 works off
daily bars, which Yahoo serves for years.

Other symbols (NQ GC HG CL NG EU BTC) are configured in `pipeline/ingest.py` but **have no data**.

## OPEN THREADS — exactly where we stopped

1. **Tampermonkey has no job in this project yet.** In gex the userscript exists to scrape Skylit.
   Here the data comes from Yahoo through the Action, so there is nothing to scrape. A userscript
   would only make sense as an *overlay* of the FuturesPulse read onto a live charting platform.
   **Unresolved — do not build one until the user says what page it should attach to.**
2. **BV volume basis (Q8).** The two source specs disagree: `Biggest Volume In` measures the
   highest-volume BAR in a wave; the BW/BV counts in the original code use a summed volume mask,
   i.e. TOTAL wave volume. This is not academic — measured on 2026-07-16, the same wave scores
   **bv 7 on total and bv 8 on peak-bar**. `beatCounts()` takes a `volumeBasis` switch so it can be
   settled without a rewrite.
3. **Daily-bar backfill.** Yahoo `1d` goes back years and would deepen Section 3's *Daily* basis
   well past 15 months. Note the asymmetry: `1d` covers the full 23h session, so it gives the Daily
   basis for free but can never give the **RTH Session** basis, which needs intraday data.
   **Not started.**
4. **ZigZag settings for other symbols.** K=3 is verified on ES only.
5. **Section 5 blockers** — still need, from the original `app.py`: the Dmd/Sply signal detection
   rules, the `E:` averaging lookback (same weekday or all sessions? fixed N?), the meaning of the
   integer in `Rly 5` / `Dmd 6`, and red-day behaviour for PT Range and the wick/body split.

## KNOWN DEFECTS IN THE ORIGINAL APP (carry forward as tests)

| # | Defect | Evidence |
|---|---|---|
| D1 | PB duration wrong in the header — shows 27m, true value **21m** | `Target Dur` (10:27→10:54) leaking into the PB field |
| D2 | `Ext` reports the wrong wave — shows 1.40, the Rly/Dmd extension is **1.63** | 1.40 belongs to a 12:42 afternoon decline |
| D3 | `Reward` duplicates `Target` | both $1,225 |
| D4 | Section 4 renders nothing | missing data |
| D5 | Coverage Test reads 0.0% | purpose undefined |
| D6 | BW/BV show 0,0 on CL | suspected volume-mask bug (Plan #176) |
| D7 | Profit Taking under-measured — 3 fields for 4h 6m, 60% of the day's range | coverage gap, not a bug |

## STANDING WORKFLOW AGREEMENTS

- **ONE AT A TIME.** Discuss one element per message. State it, give the fix, ask, stop. Do not
  list every open item and its resolution in a single reply.
- **ASK before building.** Show a mockup for anything visual.
- **Descriptive only.** No entries, stops, sizing, or trade recommendations.
- **Every statistic ships with `n` and an interval.** See the standing rule at the top.
- **Verify before claiming done.** A number that has not been checked against the original app or
  against the data is a hypothesis, not a result.

## NEXT CONCRETE STEP

Build `current/index.html` — Section 3 on the verified engine: direction with n / CI / baseline
edge, range with percentile bands, and the intraday chart with the ZigZag overlay as the engine's
visual proof.
