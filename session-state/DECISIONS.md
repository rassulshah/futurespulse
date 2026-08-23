# DECISIONS — why FuturesPulse is the way it is

Read before proposing a change to anything listed here. Each entry records what was decided, what
it was decided against, and the evidence.

---

## D-001 · The repo is the datastore, not just the code store

**Decided:** GitHub repo holds the app, the pipeline, and the market data. GitHub Actions runs the
ingestion. GitHub Pages serves the app.

**Against:** Google Drive, local-only files, a hosted backend.

**Why:** Yahoo blocks cross-origin browser requests, so the page cannot fetch market data itself.
Something server-side must do it. Drive can hold files but nothing on Drive *runs* the fetch, and
reading it from a browser needs OAuth. The Action gives storage, scheduler, and same-origin hosting
in one place, free, with version history on the data.

⚠ Unlike the gex project, **there is no Drive mirror here.** Do not create one.

---

## D-002 · 3-minute bars, and therefore a daily cadence

**Decided:** 3m bars, ingestion runs daily.

**Evidence:**

| Interval | Yahoo window |
|---|---|
| `1m` | ~7 days |
| `2m` `5m` `15m` `30m` `60m` `90m` | 60 days |
| `3m` | **does not exist** |

3m can only be resampled from 1m — 2m does not divide into 3m — and 1m expires after a week. 5m
would have been far more forgiving, but wave legs in the reference session run from 3 to 33
minutes, so 3m resolution is doing real work on the short legs.

**Consequence:** a gap longer than seven days is permanent. `ingest.py` exits non-zero on any
symbol failure rather than logging and continuing, because a silent failure quietly eats history.

---

## D-003 · Bins are midnight-anchored — do not add an origin

**Decided:** `resample("3min", label="left", closed="left")` with the default origin.

**Why:** 08:30 is 510 minutes past midnight and 510 ÷ 3 = 170 exactly, so midnight-anchored bins
land precisely on 08:30 / 08:33 / 08:36 — the same grid as the original app, with no custom origin.
Verified: 390 1m bars → 130 3m bars, grid confirmed.

---

## D-004 · Timestamps are Chicago time, and the data proves it

**Decided:** `America/Chicago` throughout; epoch-ms in storage so the browser cannot shift them.

**Evidence:** in the user's 1m export, hour 16 is completely empty while every other hour holds
~20k bars. That is the CME maintenance break at 16:00–17:00 CT. No guessing was required.

---

## D-005 · The ZigZag is K=3, and ties keep the earlier bar

**Decided:** 3-bar fractal on each side, alternation enforced, ties resolve to the earlier bar, no
minimum-move filter.

**Evidence:** every pivot in the reference session passes k=1, k=2 and k=3; **five pivots fail at
k=4**, so 3 is exactly right rather than a lower bound. The session holds 27 k=3 fractals against
24 plotted pivots — the three extras are consecutive same-type candidates, which is how alternation
was identified.

**The tie rule was decisive.** A first rebuild using `≤` scored 22/24; both misses were exact price
ties (08:36 vs 08:42 at 7681.25; 09:42 vs 09:45 at 7677.25) where the app keeps the earlier bar.
Switching to `<` gave 24/24.

**No threshold exists:** the smallest leg is 3.50 pts over 4 bars and two legs are one bar long. No
percentage or ATR filter could survive that.

---

## D-006 · The HTF context badges were cut

**Decided:** `DC<PWC`, `DC>MO`, `WC>MO` are not in the rebuild.

**Noted for the record:** these were the only conditioning variables on the Section 3 screen, and
they never fed the probability — they were display-only. Given D-007 below, they are the most
obvious place to look if the directional half is ever revived.

---

## D-007 · ⚠ The weekday does not predict direction — measured, not argued

**Decided:** nothing yet. This entry records a finding, not a decision, because it changes what
Section 3 can honestly claim.

Over **323 complete RTH sessions** (2025-03-30 → 2026-07-17):

| Weekday | n | Green | 95% CI | Edge vs baseline |
|---|---:|---:|---|---:|
| Monday | 63 | 61.9% | 49.6 – 72.9% | +7.7pp |
| Tuesday | 68 | 57.4% | 45.5 – 68.4% | +3.2pp |
| Wednesday | 67 | 47.8% | 36.3 – 59.5% | −6.4pp |
| Thursday | 63 | 46.0% | 34.3 – 58.2% | −8.1pp |
| Friday | 62 | 58.1% | 45.7 – 69.5% | +3.9pp |
| **Baseline** | **323** | **54.2%** | | |

**Every interval spans 50%.** No weekday produces a directional edge that survives its own sample
size. Monday comes closest and its lower bound is 49.6%.

The original app, looking at 6–7 sessions per weekday, displayed one weekday as **86% green**. The
same weekday across 62 sessions is **58.1%**. Same market, same definition — a 7-observation window
versus a 62-observation one.

**What this does NOT mean:** that the app should not exist. It means **weekday alone is not
carrying the directional signal**, and any verdict shown without an interval is misleading.

**Where to look next:** the D-006 badges, overnight gap direction and size, where the prior day
closed within its own range, prior-day inside/outside, volatility regime.

---

## D-008 · The range half of Section 3 survives, and the average was wrong

**Decided:** report median plus percentile bands, never a bare average.

**Evidence:** across the same 323 sessions, mean range is **71.96 pts** against a median of
**60.00** — the mean sits **20% above the typical day**. Range distributions are right-skewed, so
every "average range" figure in the original app, the 61.5 pt reference line included, systematically
overstates a normal session.

Dispersion by weekday (p25 / median / p75 / p90) is genuinely informative in a way the direction
numbers are not.

---

## D-009 · Store the primitives, derive the display values

**Decided:** persist an event log — roughly twelve session primitives — and derive all 34 Session
Details fields and all 24 header fields at render time.

**Why:** the original app computes several values twice in two places and they disagree. Defect D1
is exactly that: the header's PB duration shows 27m while Session Details and the ZigZag both say
21m, because `Target Dur` leaked into the field. One derivation path removes the entire class.

---

## D-010 · The engine computes BOTH volume bases rather than guessing

**Decided:** `waveTable()` returns `waveVolumeTotal` and `waveVolumePeakBar`; `beatCounts()` takes
a `volumeBasis` switch.

**Why:** the `Biggest Volume In` spec measures the highest-volume BAR inside a wave. The BW/BV
counts in the original code compare waves using a summed volume mask — TOTAL wave volume. These
rank waves differently. Measured on ES 2026-07-16, the same wave scores **bv 7** on total and
**bv 8** on peak-bar. Picking one silently would have been wrong half the time.

**Still open** — see OPEN THREADS item 2 in the resume note.
