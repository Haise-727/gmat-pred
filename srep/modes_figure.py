"""
Figure of the three scaling settings: which cells each scaler takes its statistics from.

Same drawing as eaai/fig1.png, but the note under it says which statistics each
setting uses: per timestep takes the mean and standard deviation, global and
grouped take the median and IQR (see fit_timestep_stats in src/ml/per_planet_train.py
and robust_stats_from_rows in src/ml/norm_ablation.py).

    python srep/modes_figure.py      # writes srep/fig_modes.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

HERE = Path(__file__).resolve().parent
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"], "mathtext.fontset": "stix"})

INK, INK_SOFT = "#111111", "#5a5a5a"
COLOR = {"per-timestep": "#2a78d6", "global": "#eb6834", "grouped": "#1baf7a"}
TITLES = {"per-timestep": "(a)  per timestep\nmean and SD from one column",
          "global": "(b)  global\nmedian and IQR from one target block",
          "grouped": "(c)  grouped\nmedian and IQR from every block"}
TARGETS, N_STEPS = ["Mercury", "Venus", "Mars"], 10

fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.15))
for ax, cond in zip(axes, COLOR):
    for ti, name in enumerate(TARGETS):
        y0 = (len(TARGETS) - 1 - ti) * 1.25
        for s in range(N_STEPS):
            inside = {"per-timestep": ti == 1 and s == 4, "global": ti == 1, "grouped": True}[cond]
            ax.add_patch(Rectangle((s, y0), 0.86, 1.0,
                                   facecolor=COLOR[cond] if inside else "#f0f0ee",
                                   edgecolor=COLOR[cond] if inside else "#d5d5d2",
                                   alpha=0.85 if inside else 1.0, linewidth=0.4))
        ax.text(-0.45, y0 + 0.5, name, ha="right", va="center", fontsize=7, color=INK)
    ax.set_xlim(-3.4, N_STEPS + 0.4); ax.set_ylim(-0.95, len(TARGETS) * 1.25 + 0.15)
    ax.set_title(TITLES[cond], fontsize=7.8, color=INK, pad=5)
    ax.axis("off")
    ax.add_patch(FancyArrowPatch((0, -0.42), (N_STEPS - 0.4, -0.42), arrowstyle="-|>",
                                 mutation_scale=6, linewidth=0.6, color=INK_SOFT))
    ax.text((N_STEPS - 0.4) / 2, -0.70, "timestep index", ha="center", va="center", fontsize=6.5, color=INK_SOFT)

fig.text(0.5, 0.015, "Each cell is every mission of one target at one timestep index. "
         "Shaded cells are the ones the scaling statistics are estimated from.",
         ha="center", va="top", fontsize=6.6, color=INK_SOFT)
fig.savefig(HERE / "fig_modes.png", dpi=300, bbox_inches="tight", pad_inches=0.02, facecolor="white")
print("wrote", HERE / "fig_modes.png")
