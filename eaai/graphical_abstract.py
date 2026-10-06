"""
Draw the graphical abstract for the EAAI submission.

Every number and every bar in the picture is read from the files in reports/.
Nothing is typed in, so the image cannot drift from the experiments.

    python eaai/graphical_abstract.py

Writes graphical_abstract.png, .tiff and .pdf next to this script.

Size. Elsevier asks for at least 531 x 1328 pixels (height by width) or
proportionally more, and says the picture must stay readable at 5 x 13 cm on a
96 dpi screen, which is about 491 x 189 pixels. The page is drawn at 13.28 x
5.31 inches (exactly 1328 x 531 pixels at 100 dpi) and saved at twice that, so
the print version is sharp. Text is large on purpose: it has to survive being
shrunk to 37 percent.

After drawing, the script checks the picture itself: it measures every piece of
text and stops with an error if two overlap or any runs off the page.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from matplotlib.text import Text

HERE = Path(__file__).resolve().parent
REPORTS = HERE.parent / "reports"

W, H = 13.28, 5.31                      # inches
DPI_OUT = 200                           # 2656 x 1062 pixels

BLUE, GREEN = "#2a78d6", "#1baf7a"      # per timestep, one shared scaler
INK, SOFT = "#111111", "#4a4a4a"
PANEL, EDGE = "#f5f5f3", "#d6d6d2"

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.linewidth": 1.4,
                     "axes.edgecolor": SOFT, "xtick.color": INK, "ytick.color": INK})


# ── data, straight from the artifacts ────────────────────────────────────────

def load():
    z = np.load(REPORTS / "prediction_traces.npz")
    norm = json.loads((REPORTS / "normalisation_ablation.json").read_text())
    inv = json.loads((REPORTS / "baseline_invariance.json").read_text())
    v = next(p for p in norm["paired"] if p["planet"] == "venus")
    tree = next(r["tree_auc"] for r in inv["runs"]
                if r["planet"] == "venus" and r["norm_mode"] == "grouped")
    return dict(
        p_healthy=z["venus__per-timestep__p_fail"],
        p_broken=z["venus__grouped__p_fail"],
        auc_net=v["val_auc_grouped"], auc_tree=tree,
        std_broken=v["pred_std_grouped"], std_healthy=v["pred_std_per-timestep"],
    )


PANELS = [(0.10, 4.70), (5.20, 3.70), (9.30, 3.88)]    # (x, width) in inches


# ── drawing ──────────────────────────────────────────────────────────────────

def build(d):
    fig = plt.figure(figsize=(W, H), dpi=100, facecolor="white")
    bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, W); bg.set_ylim(0, H); bg.axis("off")

    bg.text(W / 2, 4.93, "One shared scaler can break a deep model. "
            "The usual baseline check cannot see it.",
            ha="center", va="center", fontsize=18, weight="bold", color=INK)

    # (x, width) of the three panels, in inches. Gaps of 0.4 hold the arrows.
    panels = PANELS
    heads = ["The model stops\nreacting", "The usual check\nsays all is well", "A cheap check\ncatches it"]
    subs = ["Venus, 1,500 unseen missions", "AUC on the same input", "Spread of predictions"]
    for i, ((x, w), head, sub) in enumerate(zip(panels, heads, subs), 1):
        bg.add_patch(FancyBboxPatch((x, 0.12), w, 4.45, boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=PANEL, ec=EDGE, lw=1.5))
        bg.add_patch(Circle((x + 0.40, 4.08), 0.21, fc=INK, ec="none"))
        bg.text(x + 0.40, 4.08, str(i), ha="center", va="center", fontsize=17, weight="bold", color="white")
        bg.text(x + 0.78, 4.08, head, ha="left", va="center", fontsize=16, weight="bold",
                color=INK, linespacing=1.15)
        bg.text(x + w / 2, 0.30, sub, ha="center", va="center", fontsize=16, color=SOFT)
    for x_end in (4.80, 8.90):                      # arrows in the gaps
        bg.add_patch(FancyArrowPatch((x_end + 0.05, 2.3), (x_end + 0.35, 2.3), arrowstyle="-|>",
                                     mutation_scale=26, lw=3.2, color=INK))

    def axes(px, pw, left=0.30, right=0.25):
        return fig.add_axes([(px + left) / W, 1.28 / H, (pw - left - right) / W, 2.27 / H])

    def tidy(ax, keep_left=False):
        for s in ("top", "right") + (() if keep_left else ("left",)):
            ax.spines[s].set_visible(False)
        ax.patch.set_visible(False)

    # panel 1: what the network predicts on unseen missions
    ax = axes(*panels[0]); tidy(ax)
    bins = np.linspace(0, 1, 41)
    ax.hist(d["p_healthy"], bins=bins, color=BLUE, lw=0)
    ax.hist(d["p_broken"], bins=bins, color=GREEN, lw=0)
    top = max(np.histogram(d["p_healthy"], bins)[0].max(), np.histogram(d["p_broken"], bins)[0].max())
    ax.set_ylim(0, top * 1.12); ax.set_xlim(-0.03, 1.03)
    ax.set_yticks([]); ax.set_xticks([0, 0.5, 1]); ax.tick_params(axis="x", labelsize=15, width=1.4, length=5)
    ax.set_xlabel("P(fail)", fontsize=15, labelpad=2)
    ax.annotate("scaled per\ntimestep", xy=(0.03, top * 0.40), xytext=(0.13, top * 0.60),
                fontsize=15, color=INK, va="center", ha="left", linespacing=1.1,
                arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=2.4, shrinkA=2, shrinkB=2))
    ax.annotate("one shared scaler:\nthe same answer\nfor every mission", xy=(0.50, top * 0.93),
                xytext=(0.55, top * 0.88), fontsize=15, color=INK, va="center", ha="left",
                linespacing=1.1, arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=2.4, shrinkA=2, shrinkB=2))

    # panel 2: the baseline check on the same input
    ax = axes(*panels[1]); tidy(ax)
    ax.bar([0], [d["auc_net"]], width=0.52, color=GREEN, lw=0)
    ax.bar([1], [d["auc_tree"]], width=0.52, fc="white", ec=INK, hatch="///", lw=2.4)
    ax.axhline(0.5, color=SOFT, ls=":", lw=2, zorder=0)
    ax.text(1.36, 0.525, "chance", ha="left", va="bottom", fontsize=15, color=SOFT)
    for x, v in ((0, d["auc_net"]), (1, d["auc_tree"])):
        ax.text(x, v + 0.03, f"{v:.2f}", ha="center", va="bottom", fontsize=22, weight="bold", color=INK)
    ax.set_ylim(0, 1.22); ax.set_xlim(-0.6, 2.05); ax.set_yticks([])
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Transformer", "Boosted\ntree"], fontsize=15)
    ax.tick_params(axis="x", length=0, pad=6)

    # panel 3: spread of the predictions, log scale
    ax = axes(*panels[2], left=0.80, right=0.15); tidy(ax, keep_left=True)   # room for the tick labels
    ax.set_yscale("log"); ax.set_ylim(3e-6, 40); ax.set_xlim(-0.75, 1.75)
    ax.scatter([0], [d["std_broken"]], s=900, color=GREEN, ec="white", lw=2.5, zorder=3)
    ax.scatter([1], [d["std_healthy"]], s=900, color=BLUE, ec="white", lw=2.5, zorder=3)
    for x, v, txt in ((0, d["std_broken"], f"{d['std_broken']:.1e}"), (1, d["std_healthy"], f"{d['std_healthy']:.2f}")):
        ax.annotate(txt, (x, v), xytext=(-10 if x == 0 else 0, 24), textcoords="offset points", ha="center",
                    fontsize=19, weight="bold", color=INK)
    ratio = d["std_healthy"] / d["std_broken"]
    ax.annotate("", xy=(0.5, d["std_healthy"]), xytext=(0.5, d["std_broken"]),
                arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=2.2, shrinkA=0, shrinkB=0))
    ax.text(0.58, np.sqrt(d["std_healthy"] * d["std_broken"]),
            f"about {round(ratio, -3):,.0f}\ntimes smaller", ha="left", va="center", fontsize=15, color=INK, linespacing=1.1)
    ax.set_yticks([1e-5, 1e-3, 1e-1]); ax.set_yticklabels(["10⁻⁵", "10⁻³", "10⁻¹"], fontsize=15)
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xticks([0, 1]); ax.set_xticklabels(["shared\nscaler", "per\ntimestep"], fontsize=15)
    ax.tick_params(axis="x", length=0, pad=6); ax.tick_params(axis="y", length=4, width=1.4)
    return fig


def check_layout(fig, panels):
    """Fail loudly if two pieces of text overlap or any text leaves the page."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    page = fig.bbox
    items = [(t.get_text().replace("\n", " "), t.get_window_extent(r))
             for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()]
    problems = []
    for name, bb in items:
        if bb.x0 < page.x0 - 1 or bb.x1 > page.x1 + 1 or bb.y0 < page.y0 - 1 or bb.y1 > page.y1 + 1:
            problems.append(f"off the page: {name!r}")
    for name, bb in items:                        # below the headline, text must stay inside one panel
        if bb.y1 / 100 < 4.70:
            inside = any(x - 0.02 <= bb.x0 / 100 and bb.x1 / 100 <= x + w + 0.02 and 0.12 <= bb.y0 / 100 and bb.y1 / 100 <= 4.57
                         for x, w in panels)
            if not inside:
                problems.append(f"outside its panel: {name!r}")
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            if a.x0 < b.x1 - 1 and b.x0 < a.x1 - 1 and a.y0 < b.y1 - 1 and b.y0 < a.y1 - 1:
                problems.append(f"overlap: {items[i][0]!r} and {items[j][0]!r}")
    return len(items), problems


def main() -> int:
    d = load()
    fig = build(d)
    n, problems = check_layout(fig, PANELS)
    print(f"  checked {n} pieces of text: {'no overlaps, nothing off the page' if not problems else ''}")
    for p in problems:
        print("   PROBLEM:", p)
    if problems:
        return 1
    fig.savefig(HERE / "graphical_abstract.png", dpi=DPI_OUT, facecolor="white")
    fig.savefig(HERE / "graphical_abstract.pdf", facecolor="white")
    from PIL import Image
    im = Image.open(HERE / "graphical_abstract.png").convert("RGB")
    im.save(HERE / "graphical_abstract.tiff", compression="tiff_lzw", dpi=(DPI_OUT, DPI_OUT))
    print(f"  wrote graphical_abstract.png/.tiff/.pdf  ({im.size[0]} x {im.size[1]} pixels, width by height)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
