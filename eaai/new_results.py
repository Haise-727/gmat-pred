"""
Table rows and the figure for the diagnostic and the second dataset.

Every number is read from reports/diagnostic_eval.json and reports/second_dataset.json.

    python eaai/new_results.py        # writes fig6.png, prints both tables
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
REPORTS = HERE.parent / "reports"

plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral"], "mathtext.fontset": "stix"})

BLUE, GREEN, ORANGE, INK, SOFT = "#2a78d6", "#1baf7a", "#e8842c", "#111111", "#4a4a4a"
STATES = ["healthy", "mild", "severe", "collapsed"]
LABELS = {"healthy": "Healthy", "mild": "Mild", "severe": "Severe", "collapsed": "Collapsed"}


def load():
    ev = json.loads((REPORTS / "diagnostic_eval.json").read_text())
    cm = json.loads((REPORTS / "second_dataset.json").read_text())
    return ev, cm


def sci(x: float) -> str:
    m, e = f"{x:.2e}".split("e")
    return f"{m}e{int(e):+03d}".replace("e+0", "e+0").replace("e-0", "e-0")


def states_table() -> str:
    ev, _ = load()
    rows = []
    for s in STATES:
        v = ev["levels"][s]
        lo = f"{v['S_min']:.3f}" if v["S_min"] >= 0.01 else sci(v["S_min"])
        hi = f"{v['S_max']:.3f}" if v["S_max"] >= 0.01 else sci(v["S_max"])
        rows.append(f"{LABELS[s]} & {v['n']} & {lo} to {hi} & {v['test_auc_median']:.4f} \\\\")
    return "\n".join(rows)


def cmapss_table() -> str:
    _, cm = load()
    rows = []
    for sub in ("FD001", "FD002", "FD004"):
        for mode in ("pooled", "per-group"):
            r = [x for x in cm["runs"] if x["subset"] == sub and x["mode"] == mode]
            m = lambda k: float(np.mean([x[k] for x in r]))
            sd = lambda k: float(np.std([x[k] for x in r]))
            rows.append(f"{sub} & {mode} & {m('signal_ratio'):.3f} & ${m('test_auc'):.4f} \\pm {sd('test_auc'):.4f}$ "
                        f"& {m('tree_test_auc'):.4f} & {2 * m('pred_std_within_group'):.3f} \\\\")
    return "\n".join(rows)


def figure():
    ev, cm = load()
    thr = ev["S"]["threshold"]
    fig, ax = plt.subplots(figsize=(7.0, 3.3), dpi=200)
    rng = np.random.default_rng(0)
    rows = [("Healthy", [r["S_test"] for r in ev["runs"] if r["level"] == "healthy"], BLUE),
            ("Mild", [r["S_test"] for r in ev["runs"] if r["level"] == "mild"], BLUE),
            ("Severe", [r["S_test"] for r in ev["runs"] if r["level"] == "severe"], ORANGE),
            ("Collapsed", [r["S_test"] for r in ev["runs"] if r["level"] == "collapsed"], GREEN),
            ("Turbofan\n(second dataset)", [2 * r["pred_std_within_group"] for r in cm["runs"]], SOFT)]
    for i, (name, vals, col) in enumerate(rows[::-1]):
        y = i + rng.uniform(-0.18, 0.18, len(vals))
        ax.scatter(vals, y, s=34, color=col, alpha=0.85, lw=0)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=11)
    ax.set_xscale("log")
    ax.set_xlim(1e-5, 2)
    ax.axvline(thr, color=INK, ls="--", lw=1.3)
    ax.text(thr * 1.25, len(rows) - 0.45, "threshold, set on\nvalidation runs", fontsize=9, va="top", color=INK)
    ax.set_xlabel("Spread score S = 2 x std of P(fail), test missions", fontsize=11)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="x", labelsize=10)
    fig.tight_layout()
    fig.savefig(HERE / "fig6.png", facecolor="white")


if __name__ == "__main__":
    figure()
    print(states_table())
    print()
    print(cmapss_table())
