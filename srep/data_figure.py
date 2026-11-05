"""
Figure of the simulated telemetry, from data/per_planet/*.npz.

(a) Venus: distance from the Earth along the flight, as the percentage difference from
    the median mission, for 40 successful and 40 failed missions drawn at random. The
    shaded part is the first 40% of the flight, which is all the screen sees.
(b) Distance from the Earth for each target (median, and 5th to 95th percentile over all
    recorded steps), on a log scale. The targets differ by orders of magnitude, which is
    what a scaler pooled over a group of targets has to span.

    python srep/data_figure.py      # writes srep/fig_data.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "per_planet"
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"], "mathtext.fontset": "stix",
                     "font.size": 10, "axes.edgecolor": "#5a5a5a", "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "xtick.color": "#5a5a5a", "ytick.color": "#5a5a5a"})
INK, SOFT, GRID = "#111111", "#5a5a5a", "#d8d8d5"
SUCCESS, FAILURE = "#2a78d6", "#eb6834"      # same pair as the other figures of the paper
EARTH = 8                                     # column of earth_rmag in FEATURE_COLS, src/ml/dataset.py
TARGETS = ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]

fig, (a, b) = plt.subplots(1, 2, figsize=(10.0, 3.9), dpi=300, gridspec_kw={"width_ratios": [1.15, 1]})

z = np.load(DATA / "venus.npz")
X, y, L = z["X"], z["y"], z["lengths"]
# resample every mission to the same 100 points of its own flight, then compare with the median mission
grid = np.linspace(0, 1, 100)
R = np.array([np.interp(grid, np.arange(n) / (n - 1), X[i, :n, EARTH]) for i, n in enumerate(L)])
dev = 100 * (R - np.median(R, axis=0)) / np.median(R, axis=0)          # percent
rng = np.random.default_rng(0)
idx = np.concatenate([rng.choice(np.where(y == lab)[0], 40, replace=False) for lab in (1, 0)])
rng.shuffle(idx)
seen = set()
for i in idx:
    name, color = ("success", SUCCESS) if y[i] == 1 else ("failure", FAILURE)
    a.plot(grid, dev[i], color=color, lw=0.8, alpha=0.6, label=None if name in seen else name)
    seen.add(name)
a.axvspan(0, 0.4, color="#eeeeec", zorder=0)
a.text(0.2, 0.97, "window the screen sees", transform=a.get_xaxis_transform(), ha="center", va="top", fontsize=9, color=SOFT)
a.set_yscale("symlog", linthresh=0.01)
a.set_xlim(0, 1)
a.set_xlabel("fraction of the flight", color=INK)
a.set_ylabel("difference from the median mission (%)", color=INK)
a.set_title("(a) distance from the Earth, Venus missions", fontsize=11, color=INK, loc="left")
a.grid(axis="y", color=GRID, lw=0.5)
leg = a.legend(frameon=False, loc="lower right", fontsize=9)
for line in leg.get_lines():
    line.set_alpha(1); line.set_linewidth(2)

for k, p in enumerate(TARGETS):
    z = np.load(DATA / f"{p}.npz")
    X, L = z["X"], z["lengths"]
    v = X[np.arange(X.shape[1])[None, :] < L[:, None]][:, EARTH]
    lo, med, hi = np.percentile(v, [5, 50, 95])
    b.plot([k, k], [lo, hi], color=SOFT, lw=2, solid_capstyle="round")
    b.plot(k, med, "o", color=INK, ms=6, mec="white", mew=1.5)
b.set_yscale("log")
b.set_xticks(range(len(TARGETS)), [t.capitalize() for t in TARGETS], rotation=30)
b.set_xlim(-0.6, len(TARGETS) - 0.4)
b.set_ylabel("distance from the Earth (km)", color=INK)
b.set_title("(b) one feature across the seven targets", fontsize=11, color=INK, loc="left")
b.grid(axis="y", color=GRID, lw=0.5)
b.set_ylim(3e5, 3e10)
for x0, x1, name in ((0, 2, "inner group"), (3, 6, "outer group")):
    b.plot([x0 - 0.25, x1 + 0.25], [1.2e6, 1.2e6], color=SOFT, lw=1)
    b.text((x0 + x1) / 2, 1.5e6, name, ha="center", va="bottom", fontsize=9, color=SOFT)

fig.tight_layout(pad=0.4, w_pad=2.0)
fig.savefig(HERE / "fig_data.png", facecolor="white")
print("wrote", HERE / "fig_data.png")
