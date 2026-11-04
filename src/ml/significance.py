"""
Statistical tests for the normalisation ablation, from the saved predictions.

Reads reports/diagnostic_runs.{json,npz} and writes reports/significance.json.
Nothing is retrained. Three tests, all comparing per-timestep scaling with grouped
scaling on the same test missions:

1. Paired bootstrap of the test AUC (2,000 resamples of the test missions): a 95%
   interval for each AUC and for their difference, for every target and seed.
2. McNemar's exact test on the decisions at P(fail) >= 0.5: does the grouped model
   get a different set of missions wrong?
3. Welch's t-test across the five seeds on the test AUC, for every target. With five
   runs per group this test has little power, so it is reported as it is.

    python -m src.ml.significance
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
B = 2000


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    return float(min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5)))


def main() -> int:
    meta = json.loads((REPORTS / "diagnostic_runs.json").read_text())
    z = np.load(REPORTS / "diagnostic_runs.npz")
    planets = sorted({r["planet"] for r in meta["runs"]})
    seeds = sorted({r["seed"] for r in meta["runs"]})
    rng = np.random.default_rng(0)

    per_run = []
    for planet in planets:
        for s in seeds:
            y = z[f"{planet}__s{s}__y_test"] == 0               # failure is the positive class
            a = z[f"{planet}__per-timestep__s{s}__test"]
            g = z[f"{planet}__grouped__s{s}__test"]
            auc_a, auc_g = roc_auc_score(y, a), roc_auc_score(y, g)
            boots_a, boots_g = [], []
            n = len(y)
            for _ in range(B):
                i = rng.integers(0, n, n)
                if y[i].all() or not y[i].any():
                    continue
                boots_a.append(roc_auc_score(y[i], a[i])); boots_g.append(roc_auc_score(y[i], g[i]))
            boots_a, boots_g = np.array(boots_a), np.array(boots_g)
            diff = boots_a - boots_g
            ok_a, ok_g = (a >= 0.5) == y, (g >= 0.5) == y
            b = int((ok_a & ~ok_g).sum())        # per-timestep right, grouped wrong
            c = int((~ok_a & ok_g).sum())        # grouped right, per-timestep wrong
            per_run.append(dict(
                planet=planet, seed=s, n_test=int(n),
                auc_per_timestep=float(auc_a), auc_grouped=float(auc_g),
                ci_per_timestep=[float(np.percentile(boots_a, 2.5)), float(np.percentile(boots_a, 97.5))],
                ci_grouped=[float(np.percentile(boots_g, 2.5)), float(np.percentile(boots_g, 97.5))],
                diff=float(auc_a - auc_g),
                ci_diff=[float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))],
                mcnemar_b=b, mcnemar_c=c, mcnemar_p=mcnemar_exact(b, c),
                acc_per_timestep=float(ok_a.mean()), acc_grouped=float(ok_g.mean()),
            ))

    welch = []
    for planet in planets:
        rs = [r for r in per_run if r["planet"] == planet]
        xa = np.array([r["auc_per_timestep"] for r in rs]); xg = np.array([r["auc_grouped"] for r in rs])
        t = stats.ttest_ind(xa, xg, equal_var=False)
        welch.append(dict(planet=planet, mean_per_timestep=float(xa.mean()), sd_per_timestep=float(xa.std(ddof=1)),
                          mean_grouped=float(xg.mean()), sd_grouped=float(xg.std(ddof=1)),
                          t=float(t.statistic), p=float(t.pvalue), n_seeds=len(rs)))

    out = dict(bootstrap_resamples=B, threshold_for_mcnemar=0.5, per_run=per_run, welch_across_seeds=welch)
    (REPORTS / "significance.json").write_text(json.dumps(out, indent=1))

    print("seed 42, test missions:")
    for r in [r for r in per_run if r["seed"] == 42]:
        print(f"  {r['planet']:8s} AUC {r['auc_per_timestep']:.4f} [{r['ci_per_timestep'][0]:.4f}, {r['ci_per_timestep'][1]:.4f}]"
              f" vs {r['auc_grouped']:.4f} [{r['ci_grouped'][0]:.4f}, {r['ci_grouped'][1]:.4f}]"
              f"  diff {r['diff']:.4f} [{r['ci_diff'][0]:.4f}, {r['ci_diff'][1]:.4f}]"
              f"  McNemar b={r['mcnemar_b']} c={r['mcnemar_c']} p={r['mcnemar_p']:.2e}")
    print("all 20 target-seed pairs: difference interval excludes 0 in",
          sum(r["ci_diff"][0] > 0 for r in per_run), "; McNemar p<0.05 in", sum(r["mcnemar_p"] < 0.05 for r in per_run))
    print("Welch across five seeds:")
    for w in welch:
        print(f"  {w['planet']:8s} {w['mean_per_timestep']:.4f}±{w['sd_per_timestep']:.4f} vs {w['mean_grouped']:.4f}±{w['sd_grouped']:.4f}"
              f"  t={w['t']:.2f} p={w['p']:.2e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
