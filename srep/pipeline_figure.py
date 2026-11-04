"""
Overview figure of the screening pipeline and where each check looks.

    python srep/pipeline_figure.py      # writes srep/fig_pipeline.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral"], "mathtext.fontset": "stix"})

INK, SOFT = "#111111", "#555555"
FILL = {"data": "#e8f0fb", "prep": "#fdf0e3", "model": "#e7f6ef", "check": "#f3eefb"}
EDGE = {"data": "#2a78d6", "prep": "#e8842c", "model": "#1baf7a", "check": "#7a52c7"}

fig, ax = plt.subplots(figsize=(10.0, 4.6), dpi=220)
ax.set_xlim(0, 10); ax.set_ylim(0, 4.6); ax.axis("off")


def box(x, y, w, h, kind, title, lines):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=FILL[kind], ec=EDGE[kind], lw=1.6))
    ax.text(x + w / 2, y + h - 0.22, title, ha="center", va="top", fontsize=11.5, weight="bold", color=INK)
    ax.text(x + w / 2, y + h - 0.62, "\n".join(lines), ha="center", va="top", fontsize=9.6, color=INK, linespacing=1.35)


def arrow(x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=16, lw=1.6, color=INK))


box(0.10, 2.55, 1.95, 1.85, "data", "1. Simulation",
    ["GMAT propagates", "70,000 missions", "to 7 targets", "(success or failure)"])
box(2.35, 2.55, 1.95, 1.85, "data", "2. Telemetry",
    ["13 features per step", "about 100 steps", "the screen sees the", "first 40% of flight"])
box(4.60, 2.55, 2.25, 1.85, "prep", "3. Feature scaling",
    ["statistics taken from:", "per timestep (correct)", "one target (global)", "a group of targets (grouped)"])
box(7.15, 3.52, 2.75, 0.88, "model", "4a. Transformer screen", ["P(fail) for each mission"])
box(7.15, 2.55, 2.75, 0.88, "model", "4b. XGBoost baseline", ["same scaled arrays"])
arrow(2.05, 3.47, 2.35, 3.47); arrow(4.30, 3.47, 4.60, 3.47)
arrow(6.85, 3.70, 7.15, 3.96); arrow(6.85, 3.25, 7.15, 2.99)

box(0.10, 0.10, 3.05, 1.55, "check", "Check A: pooled AUC",
    ["one score over a group of targets", "drops from 0.9995 to 0.875,", "but hides that Venus is at 0.687"])
box(3.45, 0.10, 3.05, 1.55, "check", "Check B: tree on same input",
    ["XGBoost AUC moves by at most", "0.0002 across scalings, so it", "cannot see this fault"])
box(6.80, 0.10, 3.10, 1.55, "check", "Check C: prediction spread",
    ["S = 2 Std(P(fail)) per target,", "no labels needed at run time;", "collapsed runs sit far below the rest"])
# connector: model outputs go down to one line, then into each check
ax.plot([8.52, 8.52], [2.55, 2.05], color=INK, lw=1.6)
ax.plot([1.62, 8.52], [2.05, 2.05], color=INK, lw=1.6)
for x in (1.62, 4.97, 8.35):
    arrow(x, 2.05, x, 1.67)
ax.text(5.0, 2.12, "outputs of the screen and of the baseline", ha="center", va="bottom", fontsize=9, color=SOFT, style="italic")

fig.tight_layout(pad=0.2)
fig.savefig(HERE / "fig_pipeline.png", facecolor="white")
print("wrote", HERE / "fig_pipeline.png")
