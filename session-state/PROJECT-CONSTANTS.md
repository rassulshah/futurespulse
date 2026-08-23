# PROJECT CONSTANTS

Values that must never drift. If code and this file disagree, this file is wrong until proven
otherwise — check the verification column first.

## Session

| Constant | Value | Verified by |
|---|---|---|
| Session timezone | `America/Chicago` | hour 16 empty in the 1m export = CME 16:00–17:00 CT break |
| RTH window | 08:30 – 15:00 CT | 390 minutes, 130 3m bars |
| Bar interval | 3 minutes | 131 candles in the original app's RTH chart |
| Bin anchor | midnight (default) | 510 ÷ 3 = 170 exactly → lands on 08:30 |
| Full session | 17:00 prev → 16:00 CT | hour-histogram of the export |

## ZigZag

| Constant | Value | Verified by |
|---|---|---|
| `K` | **3** bars each side | all pivots pass k≤3; five fail at k=4 |
| Tie rule | keep the **earlier** bar | 22/24 → 24/24 |
| Minimum move | **none** | smallest leg 3.50 pts / 4 bars; two 1-bar legs |
| Confirmation lag | 3 bars = 9 minutes | fractal needs K bars on the right |

## Reference session — ES 2026-08-21

| | |
|---|---|
| Open / HOD / LOD / Close | 7687.00 / 7714.00 @10:54 / 7676.75 @08:57 / 7691.50 |
| Session range | 37.25 pts ($1,862) |
| Dmd wave | 7677.25 → 7699.75 = 22.50 pts, 09:42 → 10:06 |
| Extension | 1.633 (app shows 1.63) |
| Target wave | 7689.50 → 7714.00 = 24.50 pts, 10:27 → 10:54 (27m) |
| Pivot count | 24 interior + the 08:30 anchor |

## Yahoo

| Constant | Value |
|---|---|
| `1m` window | ~7 days |
| `2m` `5m` `15m` `30m` `60m` `90m` | 60 days |
| `3m` | does not exist |
| `1d` | years |
| Valid intervals | `1m 2m 5m 15m 30m 60m 90m 1h 1d 5d 1wk 1mo 3mo` |

## Store

```
data/{SYMBOL}/{YYYY-MM}.json     {"t":[epoch_ms],"o":[],"h":[],"l":[],"c":[],"v":[]}
data/{SYMBOL}/index.json         manifest: tz, pointValue, tickSize, months, updated
```

`t` is epoch milliseconds UTC. The manifest's `tz` is what the UI formats with — never the
viewer's local timezone.
