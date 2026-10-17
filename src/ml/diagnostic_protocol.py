"""
Protocol checks for the prediction spread diagnostic.

Reads reports/diagnostic_runs.{json,npz} and writes reports/diagnostic_protocol.json.
Nothing is retrained. It answers four questions that the first evaluation left open.

1. How much does the result depend on the AUC cutoff that defines a collapsed run?
   The cutoff of 0.85 in diagnostic_eval.py was written into the code after the AUCs
   of all runs, validation and test, had been looked at. So it is swept here, from 0.60
   to 0.95. For every cutoff the spread threshold is chosen on validation predictions
   only and then applied to the test predictions.

2. Does the result hold when the threshold is chosen on other seeds? For each seed the
   threshold is set on the validation predictions of the other four seeds, and the held
   out seed supplies the test predictions.

3. How does the spread score compare with other label-free summaries of the same
   predictions (interquartile range, range, mean binary entropy, share of predictions
   close to the median)? Compared by ROC AUC, which needs no threshold.

4. Does a pooled AUC hide the collapse? For the inner group (Mercury, Venus, Mars) the
   test predictions of the three targets are pooled, as a mixed validation set would be.

    python -m src.ml.diagnostic_protocol
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
CUTOFFS = (0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)


def binary_entropy(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(np.mean(-(p * np.log2(p) + (1 - p) * np.log2(1 - p))))


def summaries(p):
    """Each summary is oriented so that a SMALL value means a collapsed run."""
    q75, q25 = np.percentile(p, [75, 25])
    med = np.median(p)
    return {
        "S": 2.0 * float(np.std(p)),
        "iqr": float(q75 - q25),
        "range": float(p.max() - p.min()),
        "neg_entropy": -binary_entropy(p),
        "neg_share_near_median": -float(np.mean(np.abs(p - med) < 0.02)),
    }


def pick_threshold(s_pos, s_neg):
    """Middle, on a log scale, of the gap between collapsed and working runs."""
    lo, hi = max(s_pos), min(s_neg)
    return float(np.sqrt(lo * hi)) if 0 < lo < hi else float("nan")


def main() -> int:
    meta = json.loads((REPORTS / "diagnostic_runs.json").read_text())
    z = np.load(REPORTS / "diagnostic_runs.npz")
    rows = []
    for r in meta["runs"]:
        key = f"{r['planet']}__{r['norm_mode']}__s{r['seed']}"
        yk = f"{r['planet']}__s{r['seed']}"
        row = dict(planet=r["planet"], mode=r["norm_mode"], seed=r["seed"])
        for sp in ("val", "test"):
            p, y = z[f"{key}__{sp}"], z[f"{yk}__y_{sp}"]
            row[f"auc_{sp}"] = float(roc_auc_score(y == 0, p))
            for k, v in summaries(p).items():
                row[f"{k}_{sp}"] = v
        rows.append(row)

    out = {"n_runs": len(rows)}

    # 1. cutoff sweep, threshold from validation only
    sweep = []
    for c in CUTOFFS:
        pos_v = [r["S_val"] for r in rows if r["auc_val"] <= c]
        neg_v = [r["S_val"] for r in rows if r["auc_val"] > c]
        thr = pick_threshold(pos_v, neg_v)
        truth = np.array([r["auc_test"] <= c for r in rows])
        s_test = np.array([r["S_test"] for r in rows])
        entry = dict(cutoff=c, n_collapsed_val=len(pos_v), n_collapsed_test=int(truth.sum()),
                     val_separable=bool(thr == thr), threshold=thr)
        if truth.any() and not truth.all():
            entry["test_roc_auc"] = float(roc_auc_score(truth, -s_test))
        if thr == thr:
            flagged = s_test < thr
            entry.update(test_flagged=int(flagged.sum()),
                         test_missed=int((truth & ~flagged).sum()),
                         test_false_alarms=int((~truth & flagged).sum()))
        sweep.append(entry)
    out["cutoff_sweep"] = sweep

    # 2. threshold chosen on the other seeds, applied to the held out seed
    seeds = sorted({r["seed"] for r in rows})
    cv = []
    for c in CUTOFFS:
        missed = false_alarms = collapsed = n = 0
        undefined = 0
        for s in seeds:
            rest = [r for r in rows if r["seed"] != s]
            held = [r for r in rows if r["seed"] == s]
            thr = pick_threshold([r["S_val"] for r in rest if r["auc_val"] <= c],
                                 [r["S_val"] for r in rest if r["auc_val"] > c])
            if thr != thr:
                undefined += 1
                continue
            for r in held:
                t = r["auc_test"] <= c
                f = r["S_test"] < thr
                n += 1; collapsed += t
                missed += (t and not f); false_alarms += (f and not t)
        cv.append(dict(cutoff=c, seeds_without_threshold=undefined, runs_scored=n,
                       collapsed=int(collapsed), missed=int(missed), false_alarms=int(false_alarms)))
    out["leave_one_seed_out"] = cv

    # 3. other label-free summaries, ROC AUC against the test truth, no threshold needed
    alts = {}
    for name in ("S", "iqr", "range", "neg_entropy", "neg_share_near_median"):
        alts[name] = {}
        for c in CUTOFFS:
            truth = np.array([r["auc_test"] <= c for r in rows])
            if truth.any() and not truth.all():
                alts[name][str(c)] = float(roc_auc_score(truth, -np.array([r[f"{name}_test"] for r in rows])))
    out["alternative_summaries_roc_auc"] = alts

    # 4. pooled AUC across the inner group
    pooled = []
    for mode in ("per-timestep", "global", "grouped"):
        for s in seeds:
            ps, ys, per = [], [], []
            for planet in ("mercury", "venus", "mars"):
                key = f"{planet}__{mode}__s{s}"
                p, y = z[key + "__test"], z[f"{planet}__s{s}__y_test"]
                ps.append(p); ys.append(y == 0)
                per.append(float(roc_auc_score(y == 0, p)))
            pooled.append(dict(mode=mode, seed=s,
                               pooled_auc=float(roc_auc_score(np.concatenate(ys), np.concatenate(ps))),
                               mean_per_target_auc=float(np.mean(per)),
                               venus_auc=per[1]))
    out["pooled_auc_inner_group"] = pooled

    # 5. batch size: how often does a batch of n test predictions fall below the threshold?
    thr = [e["threshold"] for e in sweep if e["cutoff"] == 0.85][0]
    rng = np.random.default_rng(0)
    batch = []
    for n in (5, 10, 30, 100, 300, 1500):
        flag = {"collapsed": [], "working": []}
        for r in rows:
            key = f"{r['planet']}__{r['mode']}__s{r['seed']}"
            p = z[key + "__test"]
            kind = "collapsed" if r["auc_test"] <= 0.85 else "working"
            for _ in range(50):
                idx = rng.choice(len(p), size=min(n, len(p)), replace=False)
                flag[kind].append(2.0 * np.std(p[idx]) < thr)
        batch.append(dict(batch_size=n, collapsed_flagged=float(np.mean(flag["collapsed"])),
                          working_flagged=float(np.mean(flag["working"]))))
    out["batch_size"] = dict(threshold=thr, results=batch)

    # 6. calibration: sharpen or smooth the probabilities with a temperature T
    cal = []
    for T in (0.25, 0.5, 1.0, 2.0, 4.0):
        S_col, S_work = [], []
        for r in rows:
            key = f"{r['planet']}__{r['mode']}__s{r['seed']}"
            p = np.clip(z[key + "__test"], 1e-6, 1 - 1e-6)
            q = 1.0 / (1.0 + np.exp(-np.log(p / (1 - p)) / T))
            (S_col if r["auc_test"] <= 0.85 else S_work).append(2.0 * float(np.std(q)))
        cal.append(dict(T=T, collapsed_S_max=float(max(S_col)), working_S_min=float(min(S_work)),
                        collapsed_below_threshold=int(sum(s < thr for s in S_col)), n_collapsed=len(S_col),
                        working_below_threshold=int(sum(s < thr for s in S_work)), n_working=len(S_work)))
    out["temperature"] = dict(threshold=thr, results=cal)

    (REPORTS / "diagnostic_protocol.json").write_text(json.dumps(out, indent=1))

    print("1. cutoff sweep (threshold from validation, applied to test)")
    for e in sweep:
        print(f"   cutoff {e['cutoff']:.2f}: collapsed val/test {e['n_collapsed_val']}/{e['n_collapsed_test']}, "
              f"threshold {'none (overlap)' if not e['val_separable'] else format(e['threshold'], '.2e')}, "
              f"ROC {e.get('test_roc_auc', float('nan')):.3f}, "
              f"missed {e.get('test_missed', '-')}, false alarms {e.get('test_false_alarms', '-')}")
    print("2. leave one seed out")
    for e in cv:
        print(f"   cutoff {e['cutoff']:.2f}: no threshold on {e['seeds_without_threshold']} seeds, "
              f"collapsed {e['collapsed']}, missed {e['missed']}, false alarms {e['false_alarms']} of {e['runs_scored']}")
    print("3. ROC AUC of label-free summaries at cutoff 0.70 / 0.85 / 0.90")
    for k, v in alts.items():
        print(f"   {k:24s}", " ".join(f"{v.get(c, float('nan')):.3f}" for c in ("0.7", "0.85", "0.9")))
    print("4. pooled AUC, Mercury + Venus + Mars (mean over seeds)")
    for mode in ("per-timestep", "global", "grouped"):
        rs = [r for r in pooled if r["mode"] == mode]
        print(f"   {mode:13s} pooled {np.mean([r['pooled_auc'] for r in rs]):.4f}  "
              f"mean per target {np.mean([r['mean_per_target_auc'] for r in rs]):.4f}  "
              f"Venus alone {np.mean([r['venus_auc'] for r in rs]):.4f}")
    print("5. batch size (threshold %.2e from the 0.85 cutoff)" % thr)
    for b in batch:
        print(f"   n={b['batch_size']:5d}: collapsed batches flagged {b['collapsed_flagged']:.2f}, working batches flagged {b['working_flagged']:.3f}")
    print("6. temperature scaling of the probabilities")
    for c in cal:
        print(f"   T={c['T']:4.2f}: collapsed below threshold {c['collapsed_below_threshold']}/{c['n_collapsed']}, "
              f"working below threshold {c['working_below_threshold']}/{c['n_working']}, "
              f"max S collapsed {c['collapsed_S_max']:.1e}, min S working {c['working_S_min']:.1e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
