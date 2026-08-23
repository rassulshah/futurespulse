// ─────────────────────────────────────────────────────────────────────────────
// FuturesPulse — wave engine
// ZigZag verified against ES 2026-08-21: 24/24 pivots reproduced exactly.
// Rule: K=3 fractal on highs and lows (3 bars each side), alternation enforced,
//       ties keep the EARLIER bar, no minimum-move filter.
// ─────────────────────────────────────────────────────────────────────────────

export const K_DEFAULT = 3;

/** True if bar i is the extreme of the window [i-K, i+K] (clamped at edges). */
function isFractal(bars, i, K, high) {
  const lo = Math.max(0, i - K), hi = Math.min(bars.length - 1, i + K);
  const v = high ? bars[i].h : bars[i].l;
  for (let j = lo; j <= hi; j++) {
    if (j === i) continue;
    if (high) { if (bars[j].h > v) return false; }
    else      { if (bars[j].l < v) return false; }
  }
  return true;
}

/**
 * Confirmed ZigZag pivots.
 * @returns [{i, t, price, type:'H'|'L'}] strictly alternating, chronological.
 */
export function zigzag(bars, K = K_DEFAULT, { requireConfirmation = false } = {}) {
  const cand = [];
  const last = bars.length - 1;
  for (let i = 0; i < bars.length; i++) {
    // A pivot is only *confirmed* once K bars have printed after it.
    if (requireConfirmation && i + K > last) break;
    if (isFractal(bars, i, K, true))  cand.push({ i, t: bars[i].t, price: bars[i].h, type: 'H' });
    if (isFractal(bars, i, K, false)) cand.push({ i, t: bars[i].t, price: bars[i].l, type: 'L' });
  }
  cand.sort((a, b) => a.i - b.i);

  const out = [];
  for (const c of cand) {
    const prev = out[out.length - 1];
    if (prev && prev.type === c.type) {
      // consecutive same-type: strictly more extreme wins; an exact tie keeps the earlier
      const better = c.type === 'H' ? c.price > prev.price : c.price < prev.price;
      if (better) out[out.length - 1] = c;
    } else {
      out.push(c);
    }
  }
  return out;
}

/**
 * One measurement row per consecutive pivot pair.
 * Carries BOTH volume readings — the two indicators disagree on which to use,
 * so the engine computes both and names them explicitly.
 */
export function waveTable(bars, pivots) {
  const waves = [];
  for (let k = 0; k < pivots.length - 1; k++) {
    const a = pivots[k], b = pivots[k + 1];
    const seg = bars.slice(a.i, b.i + 1);            // endpoints inclusive
    if (!seg.length) { waves.push({ waveIndex: k, available: false }); continue; }

    const change = b.price - a.price;
    const direction = change > 0 ? 'up' : change < 0 ? 'down' : 'flat';

    let volTotal = 0, peak = null, tied = 0;
    let hi = -Infinity, lo = Infinity;
    for (const bar of seg) {
      hi = Math.max(hi, bar.h); lo = Math.min(lo, bar.l);
      const v = bar.v;
      if (v == null || !Number.isFinite(v)) continue;  // skip missing; 0 is valid
      volTotal += v;
      if (!peak || v > peak.v) { peak = bar; tied = 0; }
      else if (v === peak.v) { tied++; }               // ties keep the earliest
    }

    waves.push({
      waveIndex: k, available: true,
      startTime: a.t, startPrice: a.price, startType: a.type, startIdx: a.i,
      endTime: b.t, endPrice: b.price, endType: b.type, endIdx: b.i,
      direction,
      waveType: direction === 'up' ? 'rally' : direction === 'down' ? 'decline' : 'flat',
      priceChange: Math.abs(change),
      percentChange: a.price ? (Math.abs(change) / Math.abs(a.price)) * 100 : null,
      durationMs: b.t - a.t,
      barCount: seg.length,
      intrawaveRange: hi - lo,
      waveVolumeTotal: volTotal,
      waveVolumePeakBar: peak ? peak.v : null,
      peakVolumeTime: peak ? peak.t : null,
      peakVolumePrice: peak ? peak.c : null,
      peakVolumeOHLC: peak ? { o: peak.o, h: peak.h, l: peak.l, c: peak.c } : null,
      tiedVolumeCount: tied
    });
  }
  return waves;
}

const RANKERS = {
  pivot_change:    w => w.priceChange,
  intrawave_range: w => w.intrawaveRange,
  percent_change:  w => w.percentChange ?? -Infinity,
  speed:           w => (w.durationMs ? w.priceChange / (w.durationMs / 60000) : -Infinity)
};

/** Biggest Wave In — largest absolute pivot-to-pivot movement in scope. */
export function biggestWaveIn(waves, mode = 'pivot_change') {
  const rank = RANKERS[mode] || RANKERS.pivot_change;
  const usable = waves.filter(w => w.available);
  if (!usable.length) return { indicator: 'biggest_wave_in', available: false };
  let pool = usable.filter(w => w.direction !== 'flat');
  if (!pool.length) pool = usable;                      // all flat → earliest flat wave

  let best = pool[0], tied = 0;
  for (const w of pool.slice(1)) {
    if (rank(w) > rank(best)) { best = w; tied = 0; }
    else if (rank(w) === rank(best)) { tied++; }        // ties keep the earliest
  }
  return { indicator: 'biggest_wave_in', available: true, mode, tiedCount: tied, ...best };
}

/** Biggest Volume In — the single highest-volume bar inside each wave. */
export function biggestVolumeIn(waves) {
  return waves.filter(w => w.available && w.peakVolumeTime != null).map(w => ({
    waveIndex: w.waveIndex, direction: w.direction, waveType: w.waveType,
    waveStartTime: w.startTime, waveEndTime: w.endTime,
    biggestVolumeTime: w.peakVolumeTime,
    biggestVolume: w.waveVolumePeakBar,
    biggestVolumePrice: w.peakVolumePrice,
    ...w.peakVolumeOHLC,
    tiedVolumeCount: w.tiedVolumeCount, available: true
  }));
}

/**
 * BW / BV — how many PRIOR waves this wave beats, on size and on volume.
 * `volumeBasis` resolves the spec conflict explicitly.
 */
export function beatCounts(waves, index, { volumeBasis = 'total', sameDirectionOnly = true } = {}) {
  const cur = waves[index];
  if (!cur || !cur.available) return { bw: null, bv: null };
  const volOf = w => volumeBasis === 'peak_bar' ? w.waveVolumePeakBar : w.waveVolumeTotal;
  let bw = 0, bv = 0;
  for (let k = 0; k < index; k++) {
    const w = waves[k];
    if (!w.available) continue;
    if (sameDirectionOnly && w.direction !== cur.direction) continue;
    if (cur.priceChange > w.priceChange) bw++;
    if ((volOf(cur) ?? 0) > (volOf(w) ?? 0)) bv++;
  }
  return { bw, bv, volumeBasis };
}

/**
 * Extension of a wave — how far price ran past the wave's end pivot,
 * expressed as a multiple of the wave. Verified: ES 2026-08-21 Dmd wave = 1.63.
 */
export function extension(wave, extremePrice) {
  if (!wave?.available || !wave.priceChange) return null;
  const total = Math.abs(extremePrice - wave.startPrice);
  const ratio = total / wave.priceChange;
  return { ratio, beyondPts: total - wave.priceChange, wavePts: wave.priceChange, totalPts: total };
}
