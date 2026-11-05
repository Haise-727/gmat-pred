"""
Signal ratio against validation AUC for the seed 42 ablation (Figure 5 of the Springer version).

Same drawing as eaai/fig3.png, but the signal ratio counts at each step only the missions
that reach it (reports/signal_ratio_valid.json), which lowers the Mars values that padded
rows had raised. The AUCs come from reports/normalisation_ablation.json.

    python srep/signal_figure.py      # writes srep/fig3.png
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
REPORTS = HERE.parent / "reports"
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"], "mathtext.fontset": "stix",
                     "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
                     "legend.fontsize": 7.5, "axes.edgecolor": "#5a5a5a", "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                     "xtick.color": "#5a5a5a", "ytick.color": "#5a5a5a", "grid.color": "#d8d8d5", "grid.linewidth": 0.5})
INK, SOFT = "#111111", "#5a5a5a"
MODES = ["per-timestep", "global", "grouped"]
COLOR = {"per-timestep": "#2a78d6", "global": "#eb6834", "grouped": "#1baf7a"}
MARK = {"per-timestep": "o", "global": "s", "grouped": "D"}
LABEL = {"per-timestep": "per timestep", "global": "global", "grouped": "grouped"}

abl = json.loads((REPORTS / "normalisation_ablation.json").read_text())["paired"]
sig = {(r["planet"], r["norm_mode"]): r["signal_observed"]
       for r in json.loads((REPORTS / "signal_ratio_valid.json").read_text())["runs"] if r["seed"] == 42}

fig, ax = plt.subplots(figsize=(3.45, 2.5), dpi=600)
for p in abl:
    xs = [sig[(p["planet"], m)] for m in MODES]
    ys = [p[f"val_auc_{m}"] for m in MODES]
    ax.plot(xs, ys, "-", color=SOFT, linewidth=0.5, alpha=0.5, zorder=1)
    for m, x, y in zip(MODES, xs, ys):
        ax.scatter(x, y, s=26, marker=MARK[m], color=COLOR[m], edgecolor="white", linewidth=0.5, zorder=3)
    worst = min(range(3), key=lambda k: ys[k])
    crowded = ys[worst] > 0.99
    ax.annotate(p["planet"].capitalize(), (xs[worst], ys[worst]), textcoords="offset points",
                xytext=(0, 9) if crowded else (7, -1), ha="center" if crowded else "left",
                fontsize=6.8, color=INK, va="center")
ax.set_xscale("log")
ax.set_xlabel("signal ratio in the observed window  (log)")
ax.set_ylabel("validation AUC")
ax.grid(alpha=0.6)
ax.set_axisbelow(True)
ax.set_ylim(0.46, 1.06)
ax.axhline(0.5, color=SOFT, linewidth=0.5, linestyle=":")
ax.text(ax.get_xlim()[0] * 1.15, 0.507, "chance", ha="left", va="bottom", fontsize=6.4, color=SOFT)
handles = [plt.Line2D([], [], marker=MARK[m], linestyle="", color=COLOR[m], markersize=4.5, label=LABEL[m]) for m in MODES]
ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(1.0, 0.10), handletextpad=0.4, borderpad=0.2, labelspacing=0.3)
fig.savefig(HERE / "fig3.png", bbox_inches="tight", pad_inches=0.02, facecolor="white")
print("wrote", HERE / "fig3.png")
