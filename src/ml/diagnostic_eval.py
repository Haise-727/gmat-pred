"""
Score the prediction-spread diagnostic.

Reads reports/diagnostic_runs.{json,npz} (made by diagnostic_runs.py) and, if it
exists, reports/second_dataset.json. Writes reports/diagnostic_eval.json.

The score. A model that has collapsed gives (almost) the same P(fail) for every
mission. So we look at how much its predictions vary:

    S = 2 * std(P(fail))           0 for a constant output, 1 at the largest
                                   spread a probability can have (half the
                                   predictions at 0, half at 1)

It needs no labels and no second model. The second score is the one from the
reviewer comments, which divides by the spread of a healthy model of the same
data:

    D = std(P(fail)) / (std(P(fail) of the healthy model) + eps)

It needs a model trained the right way first, so it is only available in an
experiment like this one, where we know which run is the healthy one.

Ground truth, from labels and independent of both scores. A run counts as
collapsed if its AUC on held-out missions of the target is 0.85 or lower, that is,
the model cannot rank missions. AUC is used because it does not depend on how many
missions fail. The cutoff sits in the largest gap in the data (the runs fall at
0.51 to 0.82, then 0.895 and above). The result at other cutoffs is also saved.

Procedure. The threshold is chosen on the VALIDATION predictions only. It is the
middle (on a log scale) of the gap between the collapsed and the working runs.
Then it is applied, unchanged, to the TEST predictions.

    python -m src.ml.diagnostic_eval
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
EPS = 1e-6
CUTOFF = 0.85
OTHER_CUTOFFS = (0.70, 0.90)


def spread_score(p: np.ndarray) -> float:
    return float(2.0 * np.std(p))


def is_collapsed(auc: float, cutoff: float = CUTOFF) -> bool:
    return bool(auc <= cutoff)


def level_of(run: dict, collapsed: bool) -> str:
    if run["norm_mode"] == "per-timestep":
        return "healthy"
    if run["norm_mode"] == "global":
        return "mild"
    return "collapsed" if collapsed else "severe"


def main() -> int:
    meta = json.loads((REPORTS / "diagnostic_runs.json").read_text())
    z = np.load(REPORTS / "diagnostic_runs.npz")

    rows = []
    for r in meta["runs"]:
        key = f"{r['planet']}__{r['norm_mode']}__s{r['seed']}"
        yk = f"{r['planet']}__s{r['seed']}"
        row = dict(r)
        for split in ("val", "test"):
            p, y = z[f"{key}__{split}"], z[f"{yk}__y_{split}"]
            ref = z[f"{r['planet']}__per-timestep__s{r['seed']}__{split}"]
            row[f"S_{split}"] = spread_score(p)
            row[f"D_{split}"] = float(np.std(p) / (np.std(ref) + EPS))
            row[f"auc_{split}"] = float(roc_auc_score(y == 0, p))
            row[f"collapsed_{split}"] = is_collapsed(row[f"auc_{split}"])
        row["level"] = level_of(r, row["collapsed_test"])
        rows.append(row)

    out = dict(score="S = 2 * std(P(fail))", collapse_auc_cutoff=CUTOFF, runs=[])
    for name in ("S", "D"):
        val_pos = [r[f"{name}_val"] for r in rows if r["collapsed_val"]]
        val_neg = [r[f"{name}_val"] for r in rows if not r["collapsed_val"]]
        lo, hi = max(val_pos), min(val_neg)
        thr = float(np.sqrt(lo * hi)) if lo < hi else float("nan")
        flagged = np.array([r[f"{name}_test"] < thr for r in rows])
        truth = np.array([r["collapsed_test"] for r in rows])
        tpr = float(flagged[truth].mean()) if truth.any() else float("nan")
        fpr = float(flagged[~truth].mean())
        # ROC AUC of "low score means collapsed" on the test predictions
        roc = float(roc_auc_score(truth, -np.array([r[f"{name}_test"] for r in rows])))
        out[name] = dict(threshold=thr, val_largest_collapsed=float(lo), val_smallest_working=float(hi),
                         n_collapsed_val=len(val_pos), n_working_val=len(val_neg),
                         test_true_positive_rate=tpr, test_false_alarm_rate=fpr,
                         test_flagged=int(flagged.sum()), test_collapsed=int(truth.sum()),
                         test_runs=len(rows), test_roc_auc=roc)

    sens = {}
    for c in (CUTOFF,) + OTHER_CUTOFFS:
        truth = np.array([r["auc_test"] <= c for r in rows])
        sens[str(c)] = dict(n_collapsed=int(truth.sum()),
                            roc_auc_S=float(roc_auc_score(truth, -np.array([r["S_test"] for r in rows]))) if truth.any() else None)
    out["cutoff_sensitivity"] = sens

    # Input side: the signal ratio needs no model and no predictions. It can be
    # described but not given a clean threshold, because one run with the same
    # compression as the collapsed ones kept some ranking ability.
    col = sorted(r["signal_ratio"] for r in rows if r["collapsed_test"])
    ok = sorted((r["signal_ratio"], f"{r['planet']} {r['norm_mode']} seed {r['seed']}", r["S_test"])
                for r in rows if not r["collapsed_test"])
    out["R"] = dict(collapsed_max=col[-1], collapsed_min=col[0],
                    smallest_not_collapsed=[dict(signal_ratio=a, run=b, S_test=c) for a, b, c in ok[:3]],
                    n_below_0p01=sum(r["signal_ratio"] < 0.01 for r in rows),
                    n_below_0p01_collapsed=sum(r["signal_ratio"] < 0.01 and r["collapsed_test"] for r in rows))
    levels = {}
    for lv in ("healthy", "mild", "severe", "collapsed"):
        rs = [r for r in rows if r["level"] == lv]
        if not rs:
            continue
        s = np.array([r["S_test"] for r in rs])
        levels[lv] = dict(n=len(rs), S_min=float(s.min()), S_median=float(np.median(s)), S_max=float(s.max()),
                          test_auc_median=float(np.median([r["auc_test"] for r in rs])),
                          test_f1_median=float(np.median([r["test_f1"] for r in rs])))
    out["levels"] = levels

    # The same threshold on a dataset it was never tuned on.
    sd = REPORTS / "second_dataset.json"
    if sd.exists():
        thr = out["S"]["threshold"]
        ext = []
        for r in json.loads(sd.read_text())["runs"]:
            S = 2 * r["pred_std_within_group"]
            ext.append(dict(subset=r["subset"], mode=r["mode"], seed=r["seed"], S=S,
                            test_auc=r["test_auc"], flagged=bool(S < thr)))
        out["second_dataset"] = dict(threshold=thr, n_runs=len(ext), n_flagged=sum(e["flagged"] for e in ext),
                                     smallest_S=min(e["S"] for e in ext), runs=ext)

    out["runs"] = [{k: (round(v, 8) if isinstance(v, float) else v) for k, v in r.items()} for r in rows]
    (REPORTS / "diagnostic_eval.json").write_text(json.dumps(out, indent=1))

    print(f"threshold S (from validation): {out['S']['threshold']:.2e}   "
          f"[gap {out['S']['val_largest_collapsed']:.2e} .. {out['S']['val_smallest_working']:.2e}]")
    for name in ("S", "D"):
        o = out[name]
        print(f"{name}: test flagged {o['test_flagged']}/{o['test_runs']}, truly collapsed {o['test_collapsed']}, "
              f"TPR {o['test_true_positive_rate']:.2f}, false alarm {o['test_false_alarm_rate']:.2f}, "
              f"ROC AUC {o['test_roc_auc']:.3f}  (threshold {o['threshold']:.2e})")
    for lv, v in levels.items():
        print(f"  {lv:10s} n={v['n']:2d}  S {v['S_min']:.2e} .. {v['S_max']:.2e}  AUC {v['test_auc_median']:.4f}  F1 {v['test_f1_median']:.4f}")
    o = out["R"]
    print(f"R (signal ratio): collapsed runs {o['collapsed_min']:.4f}..{o['collapsed_max']:.4f}; "
          f"{o['n_below_0p01']} runs below 0.01, {o['n_below_0p01_collapsed']} of them collapsed; "
          f"smallest working: {o['smallest_not_collapsed'][0]['run']} at {o['smallest_not_collapsed'][0]['signal_ratio']:.4f}, then "
          f"{o['smallest_not_collapsed'][1]['signal_ratio']:.4f}")
    for c, v in sens.items():
        print(f"  cutoff {c}: {v['n_collapsed']} collapsed, ROC AUC of S {v['roc_auc_S']}")
    if "second_dataset" in out:
        s = out["second_dataset"]
        print(f"C-MAPSS: {s['n_flagged']}/{s['n_runs']} runs flagged, smallest S {s['smallest_S']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
