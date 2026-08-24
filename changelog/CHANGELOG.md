# CHANGELOG

## 2026-08-23 (later) — Section 3 shipped; bar labels were off by one

**The bars were right, the labels were wrong.** `to_3m` used `label="left"`, naming each 3m bar for
the minute it OPENS. The original app names it for the minute it CLOSES. First comparison matched
**1 of 130** bars; shifting one bar gave 130/130; re-labelling +3 minutes gave **131/131**.

Every reported time was three minutes early, and because green/red is close-vs-open, the session
open came from the wrong bar. Fixed in the pipeline (`label="right"`) and applied to all 156,236
stored bars by arithmetic — no refetch. Session bucketing now keys on each bar's START instant.

After the fix the engine reproduces the original exactly on ES 2026-08-21: all 24 pivots, the
22.50 pt Dmd wave, its **1.633** extension, the 24.50 pt / 27 min target wave.

**Section 3 is built** — `current/index.html`, no dependencies, reads the store from the same
origin. Direction as a point estimate with its 95% interval against the baseline (a proportion
near 50% is not a magnitude-from-zero quantity, so bars would misencode it); range as p10/p25/
median/p75/p90 rather than a mean. The JS statistics were cross-checked against an independent
Python implementation and agree to the digit.

⚠ **New open question — DECISIONS D-012.** The original app's session open comes from a bar
covering 08:27–08:30, one bar before the RTH open. The rebuild uses the 08:30 open. On
2026-08-21 that is GREEN vs RED. Blocking for Sections 4/5.

## 2026-08-23 — scaffold, verified wave engine, ES data loaded — NO UI YET

**The ZigZag is solved.** "3 bar high/low reversal" turned out to mean **3 bars on each side**, a
7-bar window — every pivot in the reference session passes k≤3 while five fail at k=4, so 3 is
exact rather than a lower bound. The rule that took the rebuild from 22/24 to **24/24** was tie
handling: on an exact price tie the app keeps the **earlier** bar. Both misses were ties.

`engine/zigzag.js` reproduces the original app's output on ES 2026-08-21:

    pivots           24/24 interior + the 08:30 anchor
    Dmd wave         22.50 pts / 9 bars    09:42 → 10:06
    extension        1.633                 app chart shows 1.63
    target wave      24.50 pts / 27 min    Session Details: 24.50 / 27m

The extension matching to three digits is the meaningful part — it means the wave *boundaries* are
right, not just the pivot times.

**Data.** The user's 1m ES export (460,784 bars, 2025-03-30 → 2026-07-17) imported clean: zero
duplicates, zero nulls, zero OHLC violations, zero zero-volume bars. Resampled to **153,959 3m
bars** across 17 monthly partitions, 7.2 MB. Timestamps confirmed as Chicago time by the empty
16:00 hour.

**Pipeline.** `ingest.py` + a daily Action, both written. The resample half is proven — 390 1m →
130 3m on the correct grid. ⚠ **The Yahoo fetch has never run**; the sandbox's egress proxy blocks
Yahoo, so the first Action run is the real test.

**⚠ The finding that matters most.** Across 323 complete RTH sessions, **no weekday shows a
directional edge that survives its own sample size** — every 95% interval spans 50%. The original
app displayed one weekday as 86% green off 6 observations; the same weekday across 62 sessions is
58.1%. Separately, mean range (71.96) sits 20% above median range (60.00), so every "average range"
figure in the original overstates a normal day. See DECISIONS D-007 and D-008.

**NOT BUILT:** `current/index.html`. No UI exists yet.
