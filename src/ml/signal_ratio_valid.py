"""
Signal ratio over observed steps only.

norm_ablation.signal_ratio takes the standard deviation over every row at each step,
padded rows included. Mars is the only target with missions shorter than the observed
window (18 missions shorter than 40 steps), so its padded zero rows were counted and its
ratio came out too high. This script recomputes the ratio for the seed 42 ablation and
for the 60 runs of diagnostic_runs, counting at each step only the missions that reach
it. Nothing is retrained: the scaling statistics are rebuilt from the same split and seed.

Writes reports/signal_ratio_valid.json with both values for every run.

    python -m src.ml.signal_ratio_valid
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.ml.norm_ablation import group_of, grouped_stats, signal_ratio
from src.ml.per_planet_train import apply_timestep_norm, fit_norm_stats
from src.ml.planet_config import OPERATING_FRAC
from src.ml.splits import train_val_test

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "per_planet"
PLANETS = ["venus", "mars", "mercury", "jupiter"]
MODES = ["per-timestep", "global", "grouped"]
SEEDS = [42, 0, 1, 2, 3]


def signal_ratio_observed(X: np.ndarray, lengths: np.ndarray, mu, sd) -> float:
    """Same as norm_ablation.signal_ratio, but each step only counts the missions that reach it."""
    Xn = apply_timestep_norm(X, mu, sd)
    L = Xn.shape[1]
    lo, hi = 1, max(2, int(OPERATING_FRAC * L))
    return float(np.mean([Xn[lengths > t, t, :].std(axis=0).mean() for t in range(lo, hi)]))


def main() -> int:
    rows = []
    for seed in SEEDS:
        for planet in PLANETS:
            z = np.load(DATA / f"{planet}.npz")
            X, lengths = z["X"], z["lengths"]
            tr, _, _ = train_val_test(len(z["y"]), seed)
            window = max(2, int(OPERATING_FRAC * X.shape[1]))
            for mode in MODES:
                if mode == "grouped":
                    mu, sd = grouped_stats(planet, group_of(planet), DATA, seed, X.shape[1])
                else:
                    mu, sd = fit_norm_stats(X[tr], lengths[tr], mode)
                rows.append(dict(seed=seed, planet=planet, norm_mode=mode,
                                 short_missions=int((lengths < window).sum()),
                                 signal_all_rows=round(signal_ratio(X, lengths, mu, sd), 8),
                                 signal_observed=round(signal_ratio_observed(X, lengths, mu, sd), 8)))
                r = rows[-1]
                print(f"seed {seed:>2} {planet:8} {mode:13} all rows {r['signal_all_rows']:.4f}  "
                      f"observed {r['signal_observed']:.4f}  (short missions {r['short_missions']})")
    (ROOT / "reports" / "signal_ratio_valid.json").write_text(json.dumps(dict(
        description="signal ratio with padded rows (all_rows, as reported before) and over observed rows only",
        window_frac=OPERATING_FRAC, runs=rows), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
