"""
Every figure in the paper, rendered from the measured artifacts in reports/.

Same rule as build_paper.py: nothing here contains a hand-typed number. If a
figure disagrees with a table, the artifact changed and both are stale — re-run
the experiment, do not edit the plot.

    reports/normalisation_ablation.json   src/ml/norm_ablation.py
    reports/baseline_invariance.json      src/ml/baseline_invariance.py
    reports/rare_mode_sweep.json          src/ml/rare_mode_sweep.py
    reports/prune_economics.json          src/ml/prune_economics.py
    reports/prediction_traces.npz         docs/paper/collect_traces.py
    reports/multiseed_paper/*.json        the multi-seed replication

Output goes to docs/paper/figures/ as both PDF (vector, for LaTeX) and PNG at
300 dpi (for the .docx build and for previewing).

Design constraints, so the figures survive an IEEE print run:
  * Three-hue categorical palette, assigned to the three normalisation
    conditions and never re-assigned — colour follows the condition, not its
    rank in a given chart. Validated for colour-vision deficiency.
  * Every series also carries a marker or hatch, so nothing depends on colour
    alone once the paper is photocopied in greyscale.
  * No dual axes anywhere. Two quantities of different scale get two panels.
  * Serif type (STIX, Times-metric) to sit beside IEEE body text.

Usage:
    python docs/paper/figures.py
    python docs/paper/figures.py --only fig2
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

REPO = Path(__file__).resolve().parents[2]
REPORTS = REPO / "reports"
FIGDIR = Path(__file__).resolve().parent / "figures"

# ── Palette ──────────────────────────────────────────────────────────────────
# Three categorical slots, in fixed order, one per normalisation condition.
# Checked with the data-viz validator (all-pairs, light surface): worst CVD
# deltaE 9.2, worst normal-vision deltaE 24.0 — both clear of the floors.
C_TIMESTEP = "#2a78d6"   # per-timestep  — the production configuration
C_GLOBAL   = "#eb6834"   # global        — pooled over one target's timesteps
C_GROUPED  = "#1baf7a"   # grouped       — pooled across targets (the failure)

COND_COLOR = {"per-timestep": C_TIMESTEP, "global": C_GLOBAL, "grouped": C_GROUPED}
COND_MARK  = {"per-timestep": "o", "global": "s", "grouped": "D"}
COND_HATCH = {"per-timestep": "", "global": "//", "grouped": "xx"}
CONDITIONS = ["per-timestep", "global", "grouped"]

INK      = "#111111"     # primary text
INK_SOFT = "#5a5a5a"     # secondary text / annotations
GRID     = "#d8d8d5"     # recessive grid
CRITICAL = "#c02a2a"     # reserved status colour: marks a collapsed run only
SURFACE  = "#ffffff"

# IEEE column geometry, in inches.
COL_W = 3.45
FULL_W = 7.16


def style() -> None:
    """Typography and axis defaults shared by every figure."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 8,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.5,
        "axes.edgecolor": INK_SOFT,
        "axes.linewidth": 0.6,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def load(name: str):
    p = REPORTS / name
    return json.loads(p.read_text()) if p.exists() else None


def save(fig, stem: str) -> None:
    FIGDIR.mkdir(parents=True, exist_ok=True)
    for ext, kw in (("pdf", {}), ("png", {"dpi": 300})):
        fig.savefig(FIGDIR / f"{stem}.{ext}", bbox_inches="tight",
                    pad_inches=0.02, **kw)
    plt.close(fig)
    print(f"  wrote figures/{stem}.pdf + .png")


# ═════════════════════════════════════════════════════════════════════════════
# Fig 1 — what each scaler pools over
# ═════════════════════════════════════════════════════════════════════════════

def fig1_conditions() -> None:
    """
    A schematic, not a plot: the three conditions differ only in which slice of
    the (mission x timestep x target) array the scaler statistics are estimated
    from. Stating that in words takes a paragraph and still leaves readers
    unsure; the picture settles it in one look.
    """
    fig, axes = plt.subplots(1, 3, figsize=(FULL_W, 2.15))

    targets = ["Mercury", "Venus", "Mars"]
    n_t, n_steps = len(targets), 10
    titles = [
        "(a)  per-timestep\nstatistics from one column",
        "(b)  global\nstatistics from one target block",
        "(c)  grouped\nstatistics from every block",
    ]

    for ax, cond, title in zip(axes, CONDITIONS, titles):
        colour = COND_COLOR[cond]

        # One row band per target; each band is a target's mission x timestep
        # block, drawn as a strip of cells along the flight direction.
        for ti, tname in enumerate(targets):
            y0 = (n_t - 1 - ti) * 1.25
            for s in range(n_steps):
                # Which cells the scaler pools over, per condition.
                if cond == "per-timestep":
                    inside = (ti == 1 and s == 4)
                elif cond == "global":
                    inside = (ti == 1)
                else:
                    inside = True
                ax.add_patch(Rectangle(
                    (s, y0), 0.86, 1.0,
                    facecolor=colour if inside else "#f0f0ee",
                    edgecolor=colour if inside else "#d5d5d2",
                    alpha=0.85 if inside else 1.0, linewidth=0.4))
            ax.text(-0.45, y0 + 0.5, tname, ha="right", va="center",
                    fontsize=7, color=INK)

        ax.set_xlim(-3.4, n_steps + 0.4)
        ax.set_ylim(-0.95, n_t * 1.25 + 0.15)
        ax.set_title(title, fontsize=7.8, color=INK, pad=5)
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)

        # Flight-direction arrow under the blocks.
        ax.add_patch(FancyArrowPatch((0, -0.42), (n_steps - 0.4, -0.42),
                                     arrowstyle="-|>", mutation_scale=6,
                                     linewidth=0.6, color=INK_SOFT))
        ax.text((n_steps - 0.4) / 2, -0.70, "timestep index",
                ha="center", va="center", fontsize=6.5, color=INK_SOFT)

    # The key goes at figure level. Putting it inside panel (a) collided with
    # the target labels at every font size worth using.
    fig.text(0.5, 0.015,
             "Each cell is every mission of one target at one timestep index. "
             "Shaded cells are those the scaler's median and IQR are estimated "
             "from.",
             ha="center", va="top", fontsize=6.6, color=INK_SOFT)

    save(fig, "fig1_conditions")


# ═════════════════════════════════════════════════════════════════════════════
# Fig 2 — the collapse signature, from the real held-out predictions
# ═════════════════════════════════════════════════════════════════════════════

def fig2_collapse(traces_path: Path) -> None:
    """
    The evidence that "collapse" is the right word. A low AUC could be ordinary
    underfitting; a held-out prediction distribution three ten-thousandths wide
    could not. Left two panels share the [0,1] axis; the third is drawn on its
    own microscopic axis because on the shared one it is a single vertical line,
    which is itself worth showing — so both views appear.
    """
    if not traces_path.exists():
        print("  fig2 SKIPPED — run docs/paper/collect_traces.py first")
        return
    z = np.load(traces_path)
    planet = "venus"

    fig = plt.figure(figsize=(FULL_W, 2.3))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.05], wspace=0.34)

    for i, cond in enumerate(CONDITIONS):
        key = f"{planet}__{cond}__p_fail"
        if key not in z:
            continue
        p = z[key]
        y = z[f"{planet}__{cond}__y"]

        ax = fig.add_subplot(gs[0, i])
        bins = np.linspace(0, 1, 46)
        # Split by ground truth so the reader sees whether the two populations
        # are separated at all, not just where the mass sits.
        ax.hist(p[y == 1], bins=bins, color=COND_COLOR[cond], alpha=0.85,
                label="success", linewidth=0)
        ax.hist(p[y == 0], bins=bins, color=COND_COLOR[cond], alpha=0.38,
                hatch="///", edgecolor=COND_COLOR[cond], label="failure",
                linewidth=0.4)

        ax.set_xlim(0, 1)
        ax.set_xlabel("P(fail), held-out")
        if i == 0:
            ax.set_ylabel("missions")
        ax.grid(axis="y", alpha=0.55)
        ax.set_axisbelow(True)

        span = p.max() - p.min()
        collapsed = span < 1e-2
        ax.set_title(f"({chr(97+i)})  {cond}", fontsize=7.8,
                     color=CRITICAL if collapsed else INK, pad=4)
        note = f"range {span:.1e}"
        ax.text(0.5, 0.94, note, transform=ax.transAxes, ha="center",
                va="top", fontsize=6.6,
                color=CRITICAL if collapsed else INK_SOFT)
        if i == 0:
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.86),
                      handlelength=1.1, borderpad=0.1, labelspacing=0.25)

    # Fourth panel: the grouped condition on an axis that can actually resolve
    # it. The tick labels carry the point — six significant figures, all equal.
    key = f"{planet}__grouped__p_fail"
    if key in z:
        p = z[key]
        y = z[f"{planet}__grouped__y"]
        ax = fig.add_subplot(gs[0, 3])
        bins = np.linspace(p.min(), p.max(), 40)
        ax.hist(p[y == 1], bins=bins, color=C_GROUPED, alpha=0.85, linewidth=0)
        ax.hist(p[y == 0], bins=bins, color=C_GROUPED, alpha=0.38, hatch="///",
                edgecolor=C_GROUPED, linewidth=0.4)
        ax.set_title("(d)  grouped, magnified", fontsize=7.8, color=CRITICAL,
                     pad=4)
        ax.set_xlabel("P(fail), held-out")
        ax.grid(axis="y", alpha=0.55)
        ax.set_axisbelow(True)
        ax.set_xlim(p.min(), p.max())
        ax.set_xticks([p.min(), p.max()])
        ax.set_xticklabels([f"{p.min():.6f}", f"{p.max():.6f}"], fontsize=6.4)
        ax.text(0.5, 0.94,
                f"all {len(p):,} missions inside\na window of {p.max()-p.min():.1e}",
                transform=ax.transAxes, ha="center", va="top", fontsize=6.6,
                color=CRITICAL)

    save(fig, "fig2_collapse")


# ═════════════════════════════════════════════════════════════════════════════
# Fig 3 — signal compression against discrimination
# ═════════════════════════════════════════════════════════════════════════════

def fig3_signal_vs_auc(norm: dict) -> None:
    """
    The counter-example figure. If compression alone explained the collapse the
    points would fall on a curve; Jupiter sits at a *lower* signal ratio than
    Mercury and loses almost nothing, so they do not. Drawing it this way makes
    the negative claim in Section 3 checkable by eye.
    """
    fig, ax = plt.subplots(figsize=(COL_W, 2.5))

    for p in norm["paired"]:
        xs = [p[f"signal_{c}"] for c in CONDITIONS]
        ys = [p[f"val_auc_{c}"] for c in CONDITIONS]
        # A faint line per target ties its three conditions together, so the
        # reader tracks one target across the manipulation rather than reading
        # twelve loose points.
        ax.plot(xs, ys, "-", color=INK_SOFT, linewidth=0.5, alpha=0.5,
                zorder=1)
        for c, x, yv in zip(CONDITIONS, xs, ys):
            ax.scatter(x, yv, s=26, marker=COND_MARK[c], color=COND_COLOR[c],
                       edgecolor=SURFACE, linewidth=0.5, zorder=3)
        # Direct label at the target's worst point — the relief the palette
        # validator asks for, and it also names the outliers. Targets that
        # barely move sit inside the top-right cluster, so those labels go
        # above the point instead of beside it, where they would overprint a
        # neighbour.
        worst = int(np.argmin(ys))
        crowded = ys[worst] > 0.99
        ax.annotate(p["planet"].capitalize(), (xs[worst], ys[worst]),
                    textcoords="offset points",
                    xytext=(0, 9) if crowded else (7, -1),
                    ha="center" if crowded else "left",
                    fontsize=6.8, color=INK, va="center")

    ax.set_xscale("log")
    ax.set_xlabel("signal ratio in the observed window  (log)")
    ax.set_ylabel("validation AUC")
    ax.grid(alpha=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(0.46, 1.06)
    ax.axhline(0.5, color=INK_SOFT, linewidth=0.5, linestyle=":")
    # Left-anchored: the legend lives on the right of this panel.
    ax.text(ax.get_xlim()[0] * 1.15, 0.507, "chance", ha="left", va="bottom",
            fontsize=6.4, color=INK_SOFT)

    handles = [plt.Line2D([], [], marker=COND_MARK[c], linestyle="",
                          color=COND_COLOR[c], markersize=4.5, label=c)
               for c in CONDITIONS]
    # Lifted clear of the chance line, which otherwise strikes through the
    # bottom legend entry.
    ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(1.0, 0.10),
              handletextpad=0.4, borderpad=0.2, labelspacing=0.3)
    save(fig, "fig3_signal_vs_auc")


# ═════════════════════════════════════════════════════════════════════════════
# Fig 4 — the baseline reports success on the broken configuration
# ═════════════════════════════════════════════════════════════════════════════

def fig4_baseline_blindness(norm: dict, inv: dict) -> None:
    """
    The methodological result, as one picture: under the grouped condition the
    tree's bar is at the ceiling on every target including the one where the
    network is at chance. The arrow is drawn only where the gap is large enough
    to matter, so it points at the finding rather than decorating every bar.
    """
    tree = {(r["planet"], r["norm_mode"]): r["tree_auc"] for r in inv["runs"]}
    planets = [p["planet"] for p in norm["paired"] if (p["planet"], "grouped") in tree]

    fig, ax = plt.subplots(figsize=(COL_W, 2.35))
    x = np.arange(len(planets))
    w = 0.36

    net = [next(p["val_auc_grouped"] for p in norm["paired"] if p["planet"] == pl)
           for pl in planets]
    trees = [tree[(pl, "grouped")] for pl in planets]

    ax.bar(x - w/2, net, w, color=C_GROUPED, edgecolor=C_GROUPED,
           linewidth=0.5, label="Transformer")
    ax.bar(x + w/2, trees, w, facecolor="none", edgecolor=INK,
           linewidth=0.7, hatch="///", label="XGBoost, same array")

    for xi, (n, t) in enumerate(zip(net, trees)):
        ax.text(xi - w/2, n + 0.012, f"{n:.3f}", ha="center", fontsize=6.2,
                color=INK)
        ax.text(xi + w/2, t + 0.012, f"{t:.3f}", ha="center", fontsize=6.2,
                color=INK)
        # Only where the two models actually disagree. A double-headed arrow in
        # the gutter between the bars reads as "this distance", where an arrow
        # from one bar top to the other reads as "this became that".
        if t - n > 0.2:
            ax.annotate("", xy=(xi, t), xytext=(xi, n),
                        arrowprops=dict(arrowstyle="<|-|>", color=CRITICAL,
                                        linewidth=0.8, shrinkA=0, shrinkB=0,
                                        mutation_scale=6))
            ax.text(xi - 0.06, (t + n) / 2, f"{t-n:.2f} AUC\napart",
                    ha="right", va="center", fontsize=6.4, color=CRITICAL)

    ax.axhline(0.5, color=INK_SOFT, linewidth=0.5, linestyle=":")
    ax.text(-0.45, 0.508, "chance", ha="left", va="bottom",
            fontsize=6.4, color=INK_SOFT)
    ax.set_xticks(x)
    ax.set_xticklabels([p.capitalize() for p in planets])
    ax.set_ylabel("AUC under grouped normalisation")
    ax.set_ylim(0.4, 1.16)
    ax.grid(axis="y", alpha=0.6)
    ax.set_axisbelow(True)
    # Above the plot area: inside it, the legend either sat on the chance line
    # or on the Venus bar whichever corner it was placed in.
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2,
              handlelength=1.3, borderpad=0.2, columnspacing=1.2)
    save(fig, "fig4_baseline_blindness")


# ═════════════════════════════════════════════════════════════════════════════
# Fig 5 — resampling does not recover the rare mode
# ═════════════════════════════════════════════════════════════════════════════

def fig5_rare_mode(rare: dict) -> None:
    """
    A flat line at zero is an unusual thing to plot, and that is the point: the
    x axis spans a 19x change in how hard the sampler pushes the rare mode and
    nothing moves, while the tree on the same window sits at the ceiling.
    """
    fig, ax = plt.subplots(figsize=(COL_W, 2.25))
    xs = [r["effective_resample_factor"] for r in rare["runs"]]
    rare_rec = [r["rare_mode_recall"] for r in rare["runs"]]
    overall = [r["overall_failure_recall"] for r in rare["runs"]]

    tree_rec = rare["tree_reference"]["recall_at_0.5"]
    ax.axhline(tree_rec, color=INK, linewidth=0.9, linestyle="--")
    ax.text(xs[-1], tree_rec - 0.045,
            f"XGBoost on the identical window  (AUC {rare['tree_reference']['auc']:.4f})",
            ha="right", va="top", fontsize=6.6, color=INK)

    ax.plot(xs, overall, "-", marker="s", color=C_GLOBAL, markersize=4.5,
            linewidth=1.0, label="all failure modes")
    ax.plot(xs, rare_rec, "-", marker="D", color=C_GROUPED, markersize=4.5,
            linewidth=1.4, label=f"{rare['rare_mode']} only")

    ax.annotate(f"recall {rare_rec[-1]:.4f} at every sampling weight",
                xy=(xs[-1], rare_rec[-1]), xytext=(-6, 16),
                textcoords="offset points", ha="right", fontsize=6.6,
                color=CRITICAL,
                arrowprops=dict(arrowstyle="-", color=CRITICAL, linewidth=0.6))

    ax.set_xscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{v:.2g}x" for v in xs])
    ax.minorticks_off()
    ax.set_xlabel("effective oversampling of the rare mode")
    ax.set_ylabel("failure recall, held out")
    ax.set_ylim(-0.06, 1.12)
    ax.grid(axis="y", alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="center left", handlelength=1.5, borderpad=0.2,
              labelspacing=0.3)
    save(fig, "fig5_rare_mode")


# ═════════════════════════════════════════════════════════════════════════════
# Fig 6 — where the screen belongs
# ═════════════════════════════════════════════════════════════════════════════

def fig6_economics(econ: dict) -> None:
    """
    Two panels rather than one chart with two y-axes. Panel (a) is the trade the
    operator actually makes; panel (b) is why the weighting is not uniform — the
    per-target cost spans two orders of magnitude, so a screen's value depends
    far more on the outer targets than a per-mission average would suggest.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FULL_W, 2.5),
                                   gridspec_kw={"width_ratios": [1, 1.15],
                                                "wspace": 0.28})
    w = econ["weighted"]

    # ── (a) savings against collateral damage ────────────────────────────────
    screens = [
        ("T0\nlaunch parameters", w["compute_saved_t0"], w["false_prune_rate_t0"],
         C_TIMESTEP),
        ("T40\ntelemetry at 40%", w["compute_saved_t40"], w["false_prune_rate_t40"],
         C_GLOBAL),
        ("Cascade\nT0 then T40", w["cascade_saved"], w["cascade_false_prune"],
         C_GROUPED),
    ]
    x = np.arange(len(screens))
    bw = 0.5
    for i, (name, saved, fp, col) in enumerate(screens):
        ax1.bar(i, 100 * saved, bw, color=col, edgecolor=col, linewidth=0.5)
        ax1.text(i, 100 * saved + 1.4, f"{100*saved:.1f}%", ha="center",
                 fontsize=7, color=INK)
        # The cost of each screen, printed rather than plotted on a second axis
        # — the two quantities differ by two orders of magnitude and a twin
        # axis would invite exactly the misreading the numbers rule out.
        ax1.text(i, 2.5, f"{100*fp:.2f}%\ngood lost", ha="center",
                 fontsize=6.3, color=SURFACE, va="bottom", linespacing=1.25)
    ax1.set_xticks(x)
    ax1.set_xticklabels([s[0] for s in screens], fontsize=7)
    ax1.set_ylabel("propagation compute saved (%)")
    ax1.set_ylim(0, 78)
    ax1.grid(axis="y", alpha=0.6)
    ax1.set_axisbelow(True)
    ax1.set_title("(a)  what each screening point buys", fontsize=7.8, pad=4)

    # ── (b) the cost range the weighting reflects ────────────────────────────
    per = sorted(econ["per_planet"], key=lambda r: r["prop_days"])
    names = [r["planet"].capitalize() for r in per]
    days = [r["prop_days"] for r in per]
    y = np.arange(len(per))
    ax2.barh(y, days, 0.62, color=C_TIMESTEP, edgecolor=C_TIMESTEP,
             linewidth=0.5)
    for yi, (d, r) in enumerate(zip(days, per)):
        ax2.text(d * 1.12, yi, f"{d:,.0f} d", va="center", fontsize=6.4,
                 color=INK)
    ax2.set_yticks(y)
    ax2.set_yticklabels(names, fontsize=7)
    ax2.set_xscale("log")
    ax2.set_xlim(60, 45000)
    ax2.set_xlabel("propagation-days per mission  (log)")
    ax2.grid(axis="x", alpha=0.6)
    ax2.set_axisbelow(True)
    ax2.set_title(f"(b)  a {max(days)/min(days):.0f}x cost range across targets",
                  fontsize=7.8, pad=4)

    save(fig, "fig6_economics")


# ═════════════════════════════════════════════════════════════════════════════
# Fig 7 — multi-seed replication
# ═════════════════════════════════════════════════════════════════════════════

def fig7_multiseed(seed_dir: Path, base: dict) -> None:
    """
    Whether the collapse is a seed artifact. Every seed's four targets are drawn
    as individual points rather than as a mean with an error bar, because with
    five seeds the spread of the raw points is the honest summary and an
    interval implies more than the sample supports.
    """
    runs = sorted(seed_dir.glob("normalisation_ablation_seed*.json"))
    if not runs:
        print("  fig7 SKIPPED — no multi-seed artifacts yet")
        return

    payload = [base] + [json.loads(p.read_text()) for p in runs]
    planets = [p["planet"] for p in base["paired"]]

    fig, ax = plt.subplots(figsize=(COL_W, 2.4))
    rng = np.random.default_rng(0)

    for pi, planet in enumerate(planets):
        for cond in CONDITIONS:
            vals = []
            for rep in payload:
                hit = next((q for q in rep["paired"] if q["planet"] == planet),
                           None)
                if hit:
                    vals.append(hit[f"val_auc_{cond}"])
            if not vals:
                continue
            off = {"per-timestep": -0.24, "global": 0.0, "grouped": 0.24}[cond]
            # A little horizontal jitter so coincident seeds stay countable.
            jit = rng.uniform(-0.05, 0.05, len(vals))
            ax.scatter(np.full(len(vals), pi + off) + jit, vals, s=16,
                       marker=COND_MARK[cond], color=COND_COLOR[cond],
                       edgecolor=SURFACE, linewidth=0.4, zorder=3)

    ax.axhline(0.5, color=INK_SOFT, linewidth=0.5, linestyle=":")
    ax.text(len(planets) - 0.5, 0.513, "chance", ha="right", va="bottom",
            fontsize=6.4, color=INK_SOFT)
    ax.set_xticks(np.arange(len(planets)))
    ax.set_xticklabels([p.capitalize() for p in planets])
    ax.set_ylabel("validation AUC")
    ax.set_xlabel(f"one point per seed  (n = {len(payload)})")
    ax.grid(axis="y", alpha=0.6)
    ax.set_axisbelow(True)
    handles = [plt.Line2D([], [], marker=COND_MARK[c], linestyle="",
                          color=COND_COLOR[c], markersize=4.5, label=c)
               for c in CONDITIONS]
    # Below the axes. Any in-plot corner collides with a real point here: the
    # collapsed runs sit low-left and the healthy ones fill the top band, and
    # which corner is free changes as seeds are added.
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.24),
              ncol=3, handletextpad=0.4, borderpad=0.2, columnspacing=1.4)
    save(fig, "fig7_multiseed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="render one figure, e.g. fig2")
    args = ap.parse_args()

    style()
    norm = load("normalisation_ablation.json")
    inv = load("baseline_invariance.json")
    rare = load("rare_mode_sweep.json")
    econ = load("prune_economics.json")

    want = lambda s: args.only is None or args.only == s      # noqa: E731

    print("\n  Rendering figures ->", FIGDIR)
    if want("fig1"):
        fig1_conditions()
    if want("fig2"):
        fig2_collapse(REPORTS / "prediction_traces.npz")
    if want("fig3") and norm:
        fig3_signal_vs_auc(norm)
    if want("fig4") and norm and inv:
        fig4_baseline_blindness(norm, inv)
    if want("fig5") and rare:
        fig5_rare_mode(rare)
    if want("fig6") and econ:
        fig6_economics(econ)
    if want("fig7") and norm:
        fig7_multiseed(REPORTS / "multiseed_paper", norm)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
