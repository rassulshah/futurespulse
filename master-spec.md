# FuturesPulse — master spec

Decoded from the original Replit/Streamlit app against the reference session **ES 2026-08-21**.
Every value below was extracted from the running app's own chart data, not read off a screenshot.

A rendered view of this spec:
https://claude.ai/code/artifact/152e8a1e-c5d7-4584-b387-55abe9d722a5
**This file is canonical; the artifact is a view of it.**

---

## 1 · What the app is

A repeating intraday structure — **Trap & Accumulation → Cover → Markup → Profit Taking** — with
every session measured against it: when each phase happened, how long it took, how far it went.
Averaging those measurements produces an *expected session shape*, projected onto today and scored
live against what actually happens.

Three questions:

| | Question | Section |
|---|---|---|
| 1 | Will today close above its open? | §3 |
| 2 | How far will it travel, high to low? | §3 |
| 3 | When does each phase land? | §4 / §5 |

It is not a signal generator. It is a session-shape forecast with a live scorecard.

---

## 2 · Section 3 — Green and Red Day Expectations

### Locked definitions

| Term | Definition |
|---|---|
| Green / red day | **Close vs Open** |
| Range | **Session High − Session Low** |
| Predictor | **Weekday**, single variable |
| Verdict | **A count** of prior same-weekday sessions |

Two session bases: **RTH Session** (08:30–15:00 CT) and **Daily** (full 23h session). They use
different lookback depths in the original — RTH ≈ last 6–7 per weekday, Daily = last 10.

### Required by the rebuild

- Every figure carries `n` and a 95% interval. Weekdays whose interval spans 50% are visually muted.
- Edge vs baseline is the headline number; the raw rate is secondary.
- Range as median + p25/p75/p90, never a bare mean (see DECISIONS D-008).
- Range-remaining: realised so far vs expected remaining, in points and dollars.
- A calibration panel scoring the app's own verdicts.

⚠ See DECISIONS **D-007** before assuming the directional half has an edge to display.

---

## 3 · Section 4 — Avg Timing

Renders nothing in the original (missing data). Its intended output survives as the `E:` row in
Section 5. **Recommendation: fold into Section 5 as a data service, not a screen.**

---

## 4 · Section 5 — Today's Timing

### 4.1 The A: / E: header — 24 paired fields

`A:` is today. `E:` is the historical average, tilde-prefixed.

| # | Field | A: | E: | Meaning |
|---|---|---|---|---|
| 1 | — | Grn | — | green as expected? *(unconfirmed)* |
| 2 | — | Grn | Grn | day colour *(unconfirmed)* |
| 3 | 1st | 1st LOD | 1st LOD | which extreme printed first |
| 4 | LOD | 8:57am | ~9:10a | time of session low |
| 5 | Took | 27m | ~40m | open → LOD |
| 6 | BOP | 9m | ~6m | **Back to OPen** |
| 7 | Wick | 36m | ~42m | = Took + BOP |
| 8 | W.End | 9:06am | ~9:12am | = LOD + BOP |
| 9 | Wick% | 28% | ~41% | wick ÷ session range |
| 10 | MUD | 1h 48m | ~2h 9m | MarkUp Duration, W.End → HOD |
| 11 | Rly | 24m | ~34m | rally leg inside the markup |
| 12 | Done | 10:06am | ~10:10am | rally complete |
| 13 | PB | 10:27am | ~11:06am | pullback complete |
| 14 | Num | 1 | ~1 | retracement count |
| 15 | Ret | 46% | ~32% | retracement depth |
| 16 | Risk | $612 | ~$1,352 | 12.25 pts × $50 |
| 17 | Ext | 1.40 ($212) | ~1.70 | ⚠ **defect D2** — wrong wave |
| 18 | Tgt | 24.50pts ($1,225) | ~37.12pts | measured wave PB → HOD |
| 19 | Rwd | $1,225 | ~$1,856 | ⚠ **defect D3** — duplicates Tgt |
| 20 | Dur | 27m | ~1h 49m | PB → target |
| 21 | Time | 10:54am | ~12:55p | target hit |
| 22 | HOD | 10:54am | ~12:06p | time of session high |
| 23 | HL Gap | 1h 57m | ~2h 56m | LOD → HOD |
| 24 | HL Rng | 37.25pts ($1,862) | ~64.7pts | session high − low |

⚠ Field 13's companion "Took: 27m" in the left annotation panel is **defect D1** — the true
pullback duration is 21m.

### 4.2 Session Details — 34 fields, five cards

**WICK** — What comes first? · Took · Wick Extreme Started At · Wick Ended At · Reclaimed Open in ·
Created Wick In · Wick Amt · Wick% · Sweeping

**MU/MD (BODY)** — Markup Started at · Markup Ended at · Lasted For · Markup Amt · Markup% ·
Reached HOD at · Rly For · Rly Done · Rly Ext

**TRADING** — PB · Num · Started At · Ended At · Lasted For · Retrace · Risk · Ext · Target ·
Reward · Target Dur · Target Time

**PROFIT TAKING** — PT Started at · Lasted · Range

**SESSION** — HOD · LOD · LOD to HOD Time · Range · Target

### 4.3 Verified formulas

```
Wick Amt      = Open − LOD                    7687    − 7676.75 = 10.25
Markup Amt    = HOD  − Open                   7714    − 7687    = 27.00
Wick%         = Wick Amt ÷ Session Range      10.25 ÷ 37.25 = 28%
Markup%       = Markup Amt ÷ Session Range    27.00 ÷ 37.25 = 72%
Created Wick In = Took + BOP                  27 + 9  = 36 min
W.End         = LOD time + BOP                08:57 + 9m = 09:06
MUD           = W.End → HOD                   09:06 → 10:54 = 1h 48m
HL Gap        = LOD → HOD                     08:57 → 10:54 = 1h 57m
PT Lasted     = HOD → RTH close               10:54 → 15:00 = 4h 6m
PT Range      = HOD − CLOSE                   7714 − 7691.50 = 22.50   ← NOT the post-HOD low
Retrace       = PB depth ÷ Rly wave           10.25 ÷ 22.50 = 45.6% ≈ 46%
Risk          = entry − wave origin low       7689.50 − 7677.25 = 12.25 pts
Target        = HOD − entry                   7714 − 7689.50 = 24.50 pts
Target Dur    = PB → target                   10:27 → 10:54 = 27m
Extension     = (extreme − wave start) ÷ wave size
```

⚠ `PT Range = HOD − Close` is confirmed on an **up day only**. The post-HOD low was 7685.75 at
13:36, giving 28.25 — which does not match. Red-day behaviour is unverified.

⚠ The wick/body split summing to the range is true **by construction** — it divides the range at
the open price. The forecasting value is in the **ratio**, not the identity:
`Expected Range × Expected Markup% = expected tradeable move`.

### 4.4 Reference levels

Plotted at the open; drive both `Sweeping` and `Target`.

```
PDL 7659.00   ONL 7657.75   VAL 7677.50   Open 7687.00   VWAP 7692.65
PDH 7720.00   ONH 7704.75   VAH 7719.50   Poc  7702.00   2Poc 7736.25   WPoc 7773.00
```

- `Sweeping: VAL` — the LOD printed 0.75 below VAL and reclaimed. The field names the level swept.
- `Target: ONH, Poc` — the HOD cleared Poc and ONH but not VAH or PDH. The field lists levels reached.

### 4.5 Chart annotation vocabulary

| Label | Meaning |
|---|---|
| `Dmd` / `Sply` | AM signal class — **Dmd = bullish (demand), Sply = bearish (supply)**. On the reference session `Dmd 6 @ 10:06` marks the same pivot as step `3) Rly`. |
| `42, 33` | the **BW, BV** pair — see §5 |
| `Tst` | test |
| `Pb` | pullback marker |
| `BO` | breakout |
| `mC` | leg marker |
| `Div` | divergence, on the volume and OBV subplots |
| `1.63` | wave extension multiple |

⚠ The integer in `Rly 5` / `Rly 4` / `Dmd 6` is **undetermined**. They do not run in time order —
`Rly 5` sits at 10:54 and `Rly 4` at 14:03.

---

## 5 · Wave indicators

| Indicator | Unit | Definition |
|---|---|---|
| Biggest Wave In | a whole wave | largest absolute pivot-to-pivot movement in scope. Default rank `pivot_change`; also `intrawave_range`, `percent_change`, `speed`. |
| Biggest Volume In | one bar | highest-Volume bar inside each wave, endpoints inclusive, ties to the earliest |
| BW | a count | how many prior waves this one beats **on size** |
| BV | a count | how many prior waves this one beats **on volume** — ⚠ basis unresolved, see DECISIONS D-010 |

**Shared contract:** ZigZag pivots are the sole authority for boundaries — never re-derive, never
substitute the largest candle. Both endpoints inclusive. Direction: end > start → rally; end <
start → decline; equal → flat, and flat waves are excluded from Biggest Wave In unless all are
flat. Ties resolve earliest with a `tied_count`. Missing volume is skipped; **zero volume is valid
data**. Waves crossing a session boundary are flagged and excluded by default. Fewer than two
pivots → `available = false`; never invent boundaries. Calculation stays separate from rendering
and is deterministic on repeat runs.

**Relationship:** when a wave's BW count equals every prior wave in scope, that wave *is* the
Biggest Wave In. One per-wave measurement table serves both.

---

## 6 · Phase vocabulary — consolidate to one

The original describes one session five ways. Pick one canonical model and render every view from it.

| Chart zones | Schematic candle | Timeline strip | Left annotations | Detail cards |
|---|---|---|---|---|
| 1) TRAP & ACM | TRAP & ACM | 1) Wick | 1) LOD · 2) Rec. | WICK |
| 2) COVER | 2) COVER | 2) Rly | 3) Rly | MU/MD (BODY) |
| 3) MARKUP | 3) MU | 3) PB | 4) PB | |
| | 4) PT | 4) MU | 5) HOD · 6) MU | TRADING |
| | 5) PT | | | PROFIT TAKING |

---

## 7 · Data model — twelve primitives

```
RTH open time + price          Rly start time
LOD time + price               Rly done time
Open-reclaim time              PB end time + price
HOD time + price               Post-PT low
RTH close time + price         Reference levels (VAL VAH ONH ONL POC PDH PDL)
ZigZag pivot series            Contract point value
```

All 34 Session Details fields and all 24 header fields derive from these. See DECISIONS D-009.

---

## 8 · Contract constants

| Symbol | Yahoo | Point value | Tick |
|---|---|---:|---:|
| ES | `ES=F` | $50 | 0.25 |
| NQ | `NQ=F` | $20 | 0.25 |
| GC | `GC=F` | $100 | 0.10 |
| HG | `HG=F` | $25,000 | 0.0005 |
| CL | `CL=F` | $1,000 | 0.01 |
| NG | `NG=F` | $10,000 | 0.001 |
| EU | `6E=F` | $125,000 | 0.00005 |
| BTC | `BTC=F` | $5 | 5 |

⚠ Yahoo futures tickers are **continuous front-month**, so roll days show anomalous ranges and need
flagging or the range statistics get polluted.
