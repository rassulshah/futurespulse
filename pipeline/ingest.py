#!/usr/bin/env python3
"""
FuturesPulse — data ingestion.
 
Runs on a GitHub Actions runner (open outbound internet), NOT in the browser.
Yahoo blocks cross-origin browser requests, so the fetch has to happen here and
the result is committed to the repo for the static app to read.
 
Two hard Yahoo constraints drive the design:
  1. There is no 3m interval.  Valid: 1m 2m 5m 15m 30m 60m 90m 1h 1d …
     3m can only be built from 1m — 2m does not divide into 3m.
  2. 1m data is only served for roughly the last 7 days.
     Everything else intraday goes back 60.
 
Together those mean: capture 1m DAILY, resample to 3m, append forever.
Miss more than a week and that gap can never be backfilled.
 
Usage
  python ingest.py                     # all symbols, last 7d of 1m
  python ingest.py --symbols ES CL     # subset
  python ingest.py --seed ES file.csv  # import a historical CSV into the store
  python ingest.py --dry-run           # fetch + report, write nothing
"""
 
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
from datetime import datetime, timezone
 
import pandas as pd
import yfinance as yf
 
# ── configuration ────────────────────────────────────────────────────────────
 
SYMBOLS = {                     # our name -> Yahoo ticker
    "ES": "ES=F", "NQ": "NQ=F", "GC": "GC=F", "HG": "HG=F",
    "CL": "CL=F", "NG": "NG=F", "EU": "6E=F", "BTC": "BTC=F",
}
 
POINT_VALUE = {"ES": 50, "NQ": 20, "GC": 100, "HG": 25000,
               "CL": 1000, "NG": 10000, "EU": 125000, "BTC": 5}
 
TICK_SIZE   = {"ES": 0.25, "NQ": 0.25, "GC": 0.10, "HG": 0.0005,
               "CL": 0.01, "NG": 0.001, "EU": 0.00005, "BTC": 5}
 
SESSION_TZ  = "America/Chicago"     # RTH 08:30–15:00 CT
BAR_MINUTES = 3
# The script lives in pipeline/ but the store lives at the REPO ROOT.
# .parent is pipeline/, .parent.parent is the repo root. Getting this wrong
# does not error — it silently creates a second, empty store in pipeline/data.
DATA_DIR    = Path(__file__).resolve().parent.parent / "data"
FETCH_PERIOD = "7d"                 # the full 1m window Yahoo will serve
MAX_RETRIES  = 4
 
# ── fetch ────────────────────────────────────────────────────────────────────
 
def fetch_1m(ticker: str) -> pd.DataFrame:
    """Pull 1-minute bars, retrying on Yahoo's rate limiter."""
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            df = yf.download(ticker, period=FETCH_PERIOD, interval="1m",
                             progress=False, auto_adjust=False, prepost=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if len(df):
                return df
            last_err = "empty frame"
        except Exception as e:                       # noqa: BLE001
            last_err = e
        wait = 2 ** attempt
        print(f"    retry {attempt+1}/{MAX_RETRIES} in {wait}s ({last_err})", file=sys.stderr)
        time.sleep(wait)
    raise RuntimeError(f"{ticker}: fetch failed after {MAX_RETRIES} attempts — {last_err}")
 
 
def to_3m(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resample 1m -> 3m on a midnight-anchored grid.
 
    08:30 is 510 minutes past midnight and 510 / 3 = 170 exactly, so the default
    midnight origin puts bin boundaries on 08:30, 08:33, 08:36 … Do not change
    the origin.
 
    label="right" stamps each bar with the time it CLOSES, which is the original
    app's convention: its RTH session runs 08:33…15:00, and its Session Details
    read "LOD 8:57am", "HOD 10:54am". Left-labelling shifts every reported time
    three minutes early and — because green/red is close-vs-open — silently
    changes the session open, which can flip a day's colour.
    Verified: 131/131 bars match the original app on ES 2026-08-21.
    """
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df = df.tz_convert(SESSION_TZ)
 
    out = df.resample(f"{BAR_MINUTES}min", label="right", closed="left").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    )
    return out.dropna(subset=["Open", "High", "Low", "Close"])
 
# ── store ────────────────────────────────────────────────────────────────────
# Monthly partitions keep each daily commit to one small file instead of
# rewriting a single ever-growing blob. Columnar arrays roughly halve the size
# of an array-of-objects and load straight into typed arrays in the browser.
 
def partition_path(name: str, month: str) -> Path:
    return DATA_DIR / name / f"{month}.json"
 
 
def load_partition(name: str, month: str) -> dict:
    p = partition_path(name, month)
    if p.exists():
        return json.loads(p.read_text())
    return {"t": [], "o": [], "h": [], "l": [], "c": [], "v": []}
 
 
def merge(existing: dict, incoming: pd.DataFrame) -> tuple[dict, int]:
    """Union by timestamp. Incoming wins on conflict — later fetches are more settled."""
    rows = {t: (o, h, l, c, v) for t, o, h, l, c, v in zip(
        existing["t"], existing["o"], existing["h"],
        existing["l"], existing["c"], existing["v"])}
    before = len(rows)
 
    for ts, r in incoming.iterrows():
        epoch_ms = int(ts.timestamp() * 1000)
        rows[epoch_ms] = (
            round(float(r["Open"]), 6), round(float(r["High"]), 6),
            round(float(r["Low"]), 6),  round(float(r["Close"]), 6),
            int(r["Volume"]) if pd.notna(r["Volume"]) else 0,
        )
 
    keys = sorted(rows)
    merged = {
        "t": keys,
        "o": [rows[k][0] for k in keys], "h": [rows[k][1] for k in keys],
        "l": [rows[k][2] for k in keys], "c": [rows[k][3] for k in keys],
        "v": [rows[k][4] for k in keys],
    }
    return merged, len(keys) - before
 
 
def write_store(name: str, bars3m: pd.DataFrame, dry_run: bool) -> dict:
    added_total, months_touched = 0, []
 
    for month, chunk in bars3m.groupby(bars3m.index.strftime("%Y-%m")):
        part, added = merge(load_partition(name, month), chunk)
        added_total += added
        months_touched.append(month)
        if not dry_run:
            p = partition_path(name, month)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(part, separators=(",", ":")))
 
    months = sorted(x.stem for x in (DATA_DIR / name).glob("*.json")
                    if x.stem != "index") if (DATA_DIR / name).exists() else months_touched
 
    manifest = {
        "symbol": name, "ticker": SYMBOLS[name],
        "interval": f"{BAR_MINUTES}m", "tz": SESSION_TZ,
        "pointValue": POINT_VALUE[name], "tickSize": TICK_SIZE[name],
        "months": months,
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if not dry_run:
        (DATA_DIR / name).mkdir(parents=True, exist_ok=True)
        (DATA_DIR / name / "index.json").write_text(json.dumps(manifest, indent=2))
 
    return {"added": added_total, "months": months_touched, "manifest": manifest}
 
# ── seed import ──────────────────────────────────────────────────────────────
 
def seed(name: str, csv_path: str, dry_run: bool) -> None:
    """
    Import a historical CSV. Column names are matched case-insensitively, so most
    broker and platform exports work without editing. If the file is already 3m,
    resampling is a no-op; if it is 1m it gets folded down to 3m.
    """
    df = pd.read_csv(csv_path)
    cols = {c.lower().strip(): c for c in df.columns}
 
    def pick(*names):
        for n in names:
            if n in cols:
                return cols[n]
        return None
 
    tcol = pick("datetime", "date_time", "timestamp", "time", "date")
    if tcol is None:
        raise SystemExit(f"No timestamp column found. Saw: {list(df.columns)}")
 
    dcol = pick("date") if tcol.lower() == "time" else None
    ts = (df[dcol].astype(str) + " " + df[tcol].astype(str)) if dcol else df[tcol]
 
    df = df.rename(columns={
        pick("open", "o"): "Open",   pick("high", "h"): "High",
        pick("low", "l"): "Low",     pick("close", "c", "last"): "Close",
        pick("volume", "vol", "v"): "Volume",
    })
    df.index = pd.to_datetime(ts, format="ISO8601")
    if df.index.tz is None:
        # a naive export is exchange-local; CME is shut during both DST transitions
        df.index = df.index.tz_localize(SESSION_TZ, ambiguous="NaT", nonexistent="NaT")
        df = df[df.index.notna()]
 
    if "Volume" not in df:
        df["Volume"] = 0
 
    bars = to_3m(df[["Open", "High", "Low", "Close", "Volume"]])
    res = write_store(name, bars, dry_run)
    print(f"  seeded {name}: {len(bars)} 3m bars, {res['added']} new "
          f"({bars.index.min()} → {bars.index.max()})")
 
# ── main ─────────────────────────────────────────────────────────────────────
 
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=list(SYMBOLS))
    ap.add_argument("--seed", nargs=2, metavar=("SYMBOL", "CSV"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
 
    # A bare `--symbols` (what the workflow emits on a SCHEDULED run, where
    # inputs are empty) yields [] rather than the default — the job would then
    # exit green having ingested nothing. Fall back explicitly.
    if not args.symbols:
        args.symbols = list(SYMBOLS)
 
    if args.seed:
        seed(args.seed[0], args.seed[1], args.dry_run)
        return 0
 
    failures = []
    for name in args.symbols:
        if name not in SYMBOLS:
            print(f"  skip {name}: unknown symbol", file=sys.stderr)
            continue
        print(f"→ {name} ({SYMBOLS[name]})")
        try:
            raw = fetch_1m(SYMBOLS[name])
            bars = to_3m(raw)
            res = write_store(name, bars, args.dry_run)
            print(f"  {len(raw)} 1m → {len(bars)} 3m bars, {res['added']} new "
                  f"({bars.index.min()} → {bars.index.max()})")
        except Exception as e:                        # noqa: BLE001
            print(f"  FAILED: {e}", file=sys.stderr)
            failures.append(name)
 
    if failures:
        # Fail loudly. A silent ingestion failure becomes a permanent hole in the
        # 1m history within a week.
        print(f"\n{len(failures)} symbol(s) failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    return 0
 
 
if __name__ == "__main__":
    raise SystemExit(main())
 
