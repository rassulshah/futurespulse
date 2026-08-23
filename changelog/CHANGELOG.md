# CHANGELOG

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
