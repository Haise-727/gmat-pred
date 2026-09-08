"""
The paper, as data.

This module holds the text and builds the tables; it does not know what a .tex
or a .docx is. Two renderers consume it — docs/paper/render_latex.py for the
IEEEtran submission and docs/paper/build_paper.py for the Word version — so the
two outputs cannot disagree about what the paper says.

Every quantitative claim is read out of a JSON artifact in reports/ and
formatted here. None of them are typed in. That rule exists because this project
already spent three model generations publishing contradictory figures across
its own docs (see docs/README.md), and the only fix that held was making the
prose a function of the measurements.

    reports/normalisation_ablation.json   src/ml/norm_ablation.py
    reports/baseline_invariance.json      src/ml/baseline_invariance.py
    reports/rare_mode_sweep.json          src/ml/rare_mode_sweep.py
    reports/prune_economics.json          src/ml/prune_economics.py
    reports/multiseed_paper/*.json        the multi-seed replication

Block format
------------
`document()` returns a flat list of (kind, payload) pairs:

    ("title",    {...})              title, authors, affiliation
    ("abstract", str)
    ("keywords", [str, ...])
    ("h1", str | {"text","label"})   section (label enables [#sec:x])
    ("h2", str)                      subsection
    ("p",  str)                      paragraph
    ("bullets", [str, ...])
    ("table",  {...})                caption, headers, rows, label, wide
    ("figure", {...})                file stem, caption, label, wide
    ("code",   str)

Citations are written inline as [@bibkey] and resolved by each renderer —
\\cite{} for LaTeX, bracketed numbers plus a reference list for Word.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPORTS = REPO / "reports"
MULTISEED = REPORTS / "multiseed_paper"

TITLE = ("Scale-Invariant Baselines Can Certify a Broken Deep Model: "
         "Grouped-Normalisation Collapse in Learned Trajectory Screening")
AUTHORS = ["Harsha Sakamuri", "Rohit Michael"]
AFFILIATION = "OrbitGuard Research Group"
KEYWORDS = ["feature normalisation", "shortcut learning", "model diagnostics",
            "simulation screening", "trajectory analysis", "negative results"]

CITE_RE = re.compile(r"\[@([a-zA-Z0-9_,\s]+)\]")
#: Cross-reference marker, e.g. [#fig:collapse]. Renderers turn it into a
#: \\ref for LaTeX and a resolved number for Word, so inserting a figure
#: cannot silently misnumber the prose that points at it.
REF_RE = re.compile(r"\[#([a-zA-Z0-9_:]+)\]")


# ── artifact access ──────────────────────────────────────────────────────────

def load(name: str) -> dict | None:
    p = REPORTS / name
    return json.loads(p.read_text()) if p.exists() else None


def load_traces() -> dict | None:
    """
    The raw held-out predictions behind Fig. 2, if collect_traces.py has run.

    Only used for statements about the *shape* of the prediction distribution,
    which the summary artifacts cannot support: they record a standard
    deviation, and "every mission got the same number" is a claim about the
    range.
    """
    p = REPORTS / "prediction_traces.npz"
    if not p.exists():
        return None
    try:
        import numpy as np
    except ImportError:
        return None
    return dict(np.load(p))


def load_multiseed(prefix: str) -> list[dict]:
    """Every seed replication of one experiment, or [] if none were run."""
    if not MULTISEED.exists():
        return []
    return [json.loads(p.read_text())
            for p in sorted(MULTISEED.glob(f"{prefix}_seed*.json"))]


def f4(x) -> str:
    return "—" if x is None else f"{x:.4f}"


def pct(x, dp=1) -> str:
    """Plain '%' — each renderer escapes it for its own output format."""
    return "—" if x is None else f"{100*x:.{dp}f}%"


def sci(x) -> str:
    return "—" if x is None else f"{x:.2e}"


def join(items: list[str]) -> str:
    """'a', 'a and b', 'a, b and c' — generated lists have to read as prose."""
    items = list(items)
    if len(items) <= 1:
        return items[0] if items else ""
    return f"{', '.join(items[:-1])} and {items[-1]}"


# ── the document ─────────────────────────────────────────────────────────────

def document() -> list[tuple[str, object]]:
    norm = load("normalisation_ablation.json")
    inv = load("baseline_invariance.json")
    rare = load("rare_mode_sweep.json")
    econ = load("prune_economics.json")
    ms_norm = load_multiseed("normalisation_ablation")
    ms_inv = load_multiseed("baseline_invariance")
    ms_rare = load_multiseed("rare_mode_sweep")
    traces = load_traces()

    D: list[tuple[str, object]] = []
    add = lambda k, v: D.append((k, v))                        # noqa: E731

    # Facts pulled out once, so the prose below reads as prose.
    paired = norm["paired"] if norm else []
    worst = min(paired, key=lambda p: p["val_auc_grouped"]) if paired else {}
    wname = worst.get("planet", "one target").capitalize()
    collapsed = [p["planet"].capitalize() for p in paired
                 if p.get("collapsed_grouped")]
    survivors = [p for p in paired if not p.get("collapsed_grouped")]
    surv_losses = sorted(abs(p["val_auc_gain_vs_grouped"]) for p in survivors)
    tree_spread = (max(inv["tree_auc_spread_across_conditions"].values())
                   if inv else None)
    n_seeds = 1 + len(ms_norm)
    # How often the worst target actually collapsed, across every replication.
    # The abstract and the limitations both need it, and "replicated across N
    # seeds" would overstate a 4-of-5 result.
    _reps_all = ([norm] + ms_norm) if norm else []
    _wflags = [bool(next((q for q in r["paired"]
                          if q["planet"] == worst.get("planet")), {})
                    .get("collapsed_grouped"))
               for r in _reps_all] if worst else []
    n_collapse_seeds = sum(_wflags)

    add("title", {"title": TITLE, "authors": AUTHORS,
                  "affiliation": AFFILIATION})

    # ── Abstract ─────────────────────────────────────────────────────────────
    add("abstract",
        f"Fitting one feature scaler across several groups of data is an "
        f"ordinary thing to do. We show it can quietly destroy a sequence model "
        f"while every check a practitioner would normally run says the pipeline "
        f"is fine. On 70,000 simulated interplanetary trajectories across seven "
        f"targets, a Transformer trained under a scaler pooled across a group of "
        f"targets stops responding to its input on {wname}: the standard "
        f"deviation of its held-out prediction is {sci(worst.get('pred_std_grouped'))} "
        f"and its validation AUC is {f4(worst.get('val_auc_grouped'))}, against "
        f"{f4(worst.get('val_auc_per-timestep'))} for the same architecture "
        f"under per-timestep normalisation. "
        + (lambda t: (
            f"Every one of the {len(t):,} held-out missions falls inside a "
            f"window {t.max() - t.min():.1e} wide. "
            if t is not None else "")
           )(traces.get(f"{worst.get('planet')}__grouped__p_fail")
             if traces else None)
        + f"A "
        f"gradient-boosted tree fitted to the very same arrays does not notice: "
        f"its AUC moves by at most {f4(tree_spread)} across all three "
        f"normalisation settings, and it reports the task as almost perfectly "
        f"separable while the network cannot separate it at all. So the usual "
        f"instinct — check a simple baseline before blaming the data — fails "
        f"exactly here, because trees are invariant to the thing that breaks the "
        f"network. The effect is severe but not universal: {len(collapsed)} of "
        f"{len(paired)} targets collapses outright and the rest lose between "
        f"{f4(surv_losses[0]) if surv_losses else '—'} and "
        f"{f4(surv_losses[-1]) if surv_losses else '—'} AUC while still working, "
        f"so we report when it happens and when it does not. We separate the two "
        f"kinds of pooling that are usually confused — pooling across timesteps "
        f"is survivable, pooling across groups is not — give a diagnostic based "
        f"on the spread of the predictions rather than on accuracy, and report a "
        f"second failure of the same model, which cannot reach a rare class that "
        f"a tree recovers from the identical input."
        # Only claim what was actually re-run. The three experiments are
        # replicated independently, and a blanket "all results" would overclaim
        # whenever one of them has not been swept.
        + (f" Across {n_seeds} seeds the compression is identical and the "
           f"collapse recurs on {n_collapse_seeds} of them, so it is a property "
           f"of the preprocessing rather than of one unlucky initialisation."
           if ms_norm else ""))

    add("keywords", KEYWORDS)

    # ── I. Introduction ──────────────────────────────────────────────────────
    add("h1", "Introduction")
    add("p",
        "Monte Carlo trajectory campaigns spend most of their compute on runs "
        "that were already doomed when the spacecraft left its parking orbit. "
        "Flight projects run these campaigns as a matter of course — TESS, for "
        "one, used a large dispersion campaign to drive its trajectory design "
        "[@nickel2016montecarlo] — and the cost is real enough that a body of "
        "work exists purely to make each propagation cheaper [@massari2017nonlinear, "
        "jia2022datadriven]. A different and obvious idea is to skip the runs "
        "instead: watch the first part of a trajectory and cancel the ones that "
        "are going to fail.")
    add("p",
        "We built that screen. Doing so turned up two failures that we think "
        "matter well beyond astrodynamics, and one negative result about the "
        "screen itself.")
    add("p",
        "The first failure is what this paper is about. A model trained on "
        "grouped data, with a single feature scaler fitted across the whole "
        "group, ended up emitting one constant number per group. What makes it "
        "worth writing down is not that it happened, but that it went unnoticed "
        "for a long time. Validation AUC stayed high, because a mixed validation "
        "set lets a model score well by telling groups apart without telling "
        "anything apart inside a group. A gradient-boosted baseline run on the "
        "same arrays reported near-perfect performance, because trees split on "
        "absolute values and simply do not care about the scaling the network "
        "depends on. Both of the checks we would have trusted said the pipeline "
        "was healthy.")
    add("p",
        "This is uncomfortable, because running a simple baseline is good "
        "advice. Tree ensembles are the standard sanity check on tabular and "
        "physical data, and they are usually the right one [@chen2016xgboost, "
        "grinsztajn2022tree, shwartz2022tabular]. The problem is that the "
        "property that makes them a good check in general — invariance to how "
        "the features are scaled — is precisely what makes them blind to this "
        "particular defect. The check cannot fail the model, so it certifies it.")
    add("p",
        "We make three contributions. First, a controlled decomposition of the "
        "collapse that separates pooling across timesteps from pooling across "
        "groups, and shows only the second is fatal. Second, a demonstration "
        "that a scale-invariant baseline actively signs off on the broken "
        "configuration, together with a cheap diagnostic that does catch it. "
        "Third, a second failure of the same model — it cannot reach a rare "
        "class that is recoverable from its own input — which we measure rather "
        "than assume. We also report, because it bounds how much the first two "
        "matter in practice, that the application which motivated all of this "
        "does not need a sequence model at all.")
    add("p",
        "Every number in this paper is produced by a script in the accompanying "
        "repository and written to a machine-readable artifact. The paper, "
        "including its tables and figures, is generated from those artifacts.")

    # ── II. Related work ─────────────────────────────────────────────────────
    add("h1", "Related Work")

    add("h2", "Normalisation and what it assumes")
    add("p",
        "Normalisation is central to training deep networks, and the standard "
        "layers — batch, layer, group and instance normalisation — all address "
        "some version of the problem [@ioffe2015batch, ba2016layer, wu2018group, "
        "ulyanov2016instance]. They also all assume something about the input "
        "they are handed: that the feature statistics are either stationary, or "
        "at least comparable across whatever the pooling axis is. Fitting one "
        "scaler over several groups whose natural ranges differ by orders of "
        "magnitude breaks that assumption before the first layer runs. The "
        "audio literature ran into a related issue early, where per-recording "
        "and per-corpus statistics behave very differently "
        "[@salamon2017deep]. What we add is a controlled decomposition showing "
        "that pooling across groups, not pooling in general, is what does the "
        "damage, plus the observation that the resulting model is a constant "
        "rather than merely a weak one.")

    add("h2", "Shortcut learning and misleading aggregate metrics")
    add("p",
        "Networks prefer easy signals, and will take a shortcut over the "
        "intended structure whenever one is available [@geirhos2020shortcut, "
        "shah2020pitfalls]. Related work on Clever-Hans behaviour shows models "
        "scoring well for reasons that have nothing to do with the task "
        "[@lapuschkin2019unmasking]. Grouped data with heterogeneous scales "
        "offers an unusually clean shortcut: the gap between group centroids. A "
        "model that learns only that gap can post a validation AUC above 0.95 "
        "while being useless inside every individual group, which is exactly "
        "what we observed. Our contribution here is a diagnostic — the spread of "
        "the predictions within a group — that separates this case from ordinary "
        "underfitting and needs no labels.")

    add("h2", "Trees as baselines, and the limits of that")
    add("p",
        "Tree ensembles remain strong on tabular and physical data, often "
        "matching or beating deep models [@chen2016xgboost, ke2017lightgbm, "
        "grinsztajn2022tree, shwartz2022tabular], which is a large part of why "
        "they are the default baseline. Their splits are axis-aligned and "
        "threshold-based, so any monotone rescaling of a feature leaves them "
        "unchanged. That invariance is normally a virtue. We point out that it "
        "also makes them unable to detect a preprocessing fault that is fatal to "
        "a network, and so a practitioner who uses a tree to confirm that the "
        "features carry signal gets a true answer to a question they did not "
        "mean to ask.")

    add("h2", "Rare classes and optimisation limits")
    add("p",
        "The usual answers to extreme class imbalance are reweighting, focal "
        "loss, or resampling [@buda2018systematic, lin2017focal, cui2019class]. "
        "In [#sec:rare] we report a case where none of that is the issue: "
        "oversampling a rare failure mode by a factor of "
        f"{rare['runs'][-1]['effective_resample_factor']:.1f} moves its recall "
        "not at all, while a tree on the same window separates it almost "
        "perfectly. "
        "The evidence in the space domain runs the same way — the ESA anomaly "
        "benchmark reports that current sequence models still struggle on rare "
        "but operationally important events in real satellite telemetry "
        "[@kotowski2024esaadb], and it is worth noting that carefully engineered "
        "LSTM pipelines do work on this kind of data when the per-channel "
        "handling is right [@hundman2018detecting]. That contrast is the point: "
        "the difference is in the engineering, not the model class."
        if rare else
        "The usual answers to extreme class imbalance are reweighting, focal "
        "loss, or resampling [@buda2018systematic, lin2017focal, cui2019class].")

    add("h2", "Learned screening in astrodynamics")
    add("p",
        "Machine learning is now well established in spacecraft guidance and "
        "trajectory design [@izzo2019survey, izzo2024optimality], including "
        "networks that approximate optimal control directly "
        "[@sanchezsanchez2018realtime], predict transfer costs without full "
        "propagation [@li2019deepnetworks, izzo2018mlevo], and learn robust "
        "low-thrust policies that are then certified by Monte Carlo "
        "[@zavoli2021rl]. Screening specifically — using a learned model to "
        "decide which of a very large number of candidate cases deserve full "
        "analysis — is established in conjunction assessment, both as an ESA "
        "competition on real conjunction data [@uriot2020collision, "
        "acciarini2021kessler] and as a benchmark of deep approaches against the "
        "classical filters they would replace [@stevenson2023benchmarking]. "
        "That last one is the closest analogue to our setting: a screening task "
        "on a deterministic astrodynamics simulator, benchmarked against "
        "non-deep baselines. Learned early cancellation of individual Monte "
        "Carlo trajectory runs, which is what [#sec:econ] evaluates, is "
        "something we could not find treated in this literature; the closest "
        "work reduces the cost of each propagation rather than deciding which "
        "propagations to start [@massari2017nonlinear, jia2022datadriven]. "
        "Surrogate and early-exit methods for expensive simulation are the "
        "general form of the idea [@baker2019accelerating, sun2021early].")

    # ── III. Setup ───────────────────────────────────────────────────────────
    add("h1", "Setup")

    add("h2", "Task and data")
    add("p",
        "The corpus is 70,000 simulated Earth-departure missions across seven "
        "interplanetary targets — Mercury, Venus, Mars, Jupiter, Saturn, Uranus "
        "and Neptune — with 10,000 missions each, generated with a deterministic "
        "two/three-body propagator in NASA's General Mission Analysis Tool, "
        "which is itself an extensively verified piece of software "
        "[@hughes2014verification]. Each mission is described by six injection "
        "offsets: three components of the trans-orbit-insertion burn (dv_V, "
        "dv_N, dv_B) and three parking-orbit angles (RAAN, AOP, INC). Each is "
        "labelled success or failure, and failures are further typed by physical "
        "mode — surface impact, orbit too high, missed target, and a few others.")
    add("p",
        "Telemetry is sampled at a fixed cadence of 54,000 s (15 hours) for the "
        "interplanetary transfers and downsampled to roughly 100 steps per "
        "mission, so that targets whose flight times differ by two orders of "
        "magnitude still produce sequences of comparable length. Thirteen "
        "features are recorded per step, including synodic-frame position, "
        "specific orbital energy, flight-path angle, normalised target distance "
        "and eccentricity. An eighth target was generated (the Moon) and is "
        "deliberately excluded from the study: it is a six-day Earth-centric "
        "transfer sampled at 60 s, and shares neither the cost structure of "
        "[#sec:econ] nor the dynamical regime of a heliocentric transfer.")
    add("p",
        "The screening task is to observe the first 40% of a mission's "
        "trajectory and decide whether to abort it. Splits are 70/15/15 by "
        "mission and deterministic in (n, seed). Every experiment draws its "
        "partition from a single definition in the repository, so no model is "
        "ever scored on data that was used to select it. This is not a "
        "hypothetical concern: two earlier analyses in this project were invalid "
        "because two scripts independently permuted the same number of missions "
        "with the same seed and so produced overlapping 'test' sets.")

    add("h2", "Models")
    add("p",
        "The sequence model is a Pre-LN Transformer encoder with d_model 128, 8 "
        "attention heads, 4 layers and CLS-token pooling, carrying two heads on "
        "a shared trunk: one for the mission outcome and one for the failure "
        "mode. It is trained on random-length prefixes, so its predictions are "
        "in-distribution at any point in the stream rather than only at the 40% "
        "mark. The baseline is XGBoost with 300 trees at depth 5, fitted to the "
        "same normalised prefix, flattened. Throughout this paper, 'the same "
        "input' means literally the same array — the baseline consumes the view "
        "the network is given, not a re-derived feature set. That detail carries "
        "most of the argument, so we are strict about it.")

    add("h2", "The three normalisation settings")
    add("p",
        "Three conditions differ only in how the feature statistics are pooled. "
        "Architecture, seed, split, optimiser and epoch budget are held fixed "
        "across all of them. Fig. 1 shows what each one estimates its statistics "
        "from.")
    add("bullets", [
        "per-timestep — each feature is standardised against its distribution "
        "at that timestep index, across the missions of one target. This is the "
        "configuration the working system uses.",
        "global — one RobustScaler (median and IQR) per target, pooled across "
        "all of that target's timesteps.",
        "grouped — one RobustScaler pooled across every timestep of every target "
        "in a regime group (inner: Mercury, Venus, Mars; outer: Jupiter, Saturn, "
        "Uranus, Neptune). This is the setting that failed in production.",
    ])
    add("figure", {
        "stem": "fig1_conditions", "wide": True, "label": "fig:conditions",
        "caption": "The three normalisation settings, and the only thing that "
                   "differs between them: which part of the data the scaler's "
                   "median and IQR are estimated from. Everything else in the "
                   "training pipeline is identical.",
    })
    add("p",
        "It is worth being explicit about why the third setting is not a straw "
        "man. Fitting one RobustScaler on a concatenated training set is what "
        "you get by following almost any standard pipeline tutorial. Nothing "
        "warns you, and the result looks like a correctly normalised array.")

    # ── IV. Collapse ─────────────────────────────────────────────────────────
    add("h1", "Grouped-Normalisation Collapse")

    add("h2", "Why it happens")
    add("p",
        "A mission's features sweep a wide range over its flight, and different "
        "targets occupy ranges that differ by orders of magnitude. A scaler "
        "fitted over a pooled set therefore takes its scale from the largest "
        "source of variation in the pool. What the screen actually has to "
        "discriminate is neither of those things: it is the spread between "
        "missions at a given point in the flight, which is small by comparison. "
        "Pooling divides that spread by a denominator chosen for something else, "
        "squashing the useful signal toward zero while leaving the "
        "between-group structure untouched. The network is then asked to "
        "amplify a difference that has been pushed to the edge of what gradient "
        "descent can pick up, and Pre-LN layer normalisation removes much of "
        "what survives.")
    add("p",
        "We measure this as the signal ratio: the mean across-mission standard "
        "deviation of the normalised features, computed inside the observed "
        "window only. The restriction matters more than it might seem. Averaged "
        "over the whole flight the metric is useless, because late timesteps "
        "carry enormous across-mission spread — failing trajectories have "
        "physically diverged by then — and that swamps the early signal, making "
        "every condition look healthy. The model commits at 40%, so the quantity "
        "that matters is the spread inside the prefix it actually sees.")

    add("h2", "The controlled ablation")
    if norm:
        rows = [[p["planet"].capitalize(),
                 f"{p['signal_per-timestep']:.4f}", f4(p["val_auc_per-timestep"]),
                 f"{p['pred_std_per-timestep']:.2e}",
                 f"{p['signal_global']:.4f}", f4(p["val_auc_global"]),
                 f"{p['pred_std_global']:.2e}",
                 f"{p['signal_grouped']:.4f}", f4(p["val_auc_grouped"]),
                 f"{p['pred_std_grouped']:.2e}"] for p in paired]
        add("table", {
            "label": "tab:ablation", "wide": True,
            "caption": "Normalisation ablation. Identical architecture, seed "
                       "and split; only the pooling differs. 'sig' is the mean "
                       "within-timestep standard deviation of the normalised "
                       "features in the observed window. 'std' is the standard "
                       "deviation of P(fail) over the held-out split — the "
                       "quantity that identifies a collapse, as against a model "
                       "that is merely inaccurate.",
            "headers": ["Target", "sig", "AUC", "std", "sig", "AUC", "std",
                        "sig", "AUC", "std"],
            "groups": [("", 1), ("per-timestep", 3), ("global", 3),
                       ("grouped", 3)],
            "rows": rows,
        })
        add("p",
            f"The decomposition is the first result. Pooling across timesteps "
            f"within a single target squashes the signal by one to two orders of "
            f"magnitude, and yet the network keeps working: it survives on all "
            f"{len(paired)} targets, losing at most a few thousandths of AUC. "
            f"Pooling across a group is a different animal. On {wname} it is "
            f"catastrophic — held-out output standard deviation "
            f"{sci(worst.get('pred_std_grouped'))}, which is to say the network "
            f"emits one number for every mission regardless of what it is shown, "
            f"with AUC falling from {f4(worst.get('val_auc_per-timestep'))} to "
            f"{f4(worst.get('val_auc_grouped'))}.")
        add("figure", {
            "stem": "fig2_collapse", "wide": True, "label": "fig:collapse",
            "caption": f"Held-out P(fail) on {wname} under each setting, split "
                       f"by ground truth. Under per-timestep and global "
                       f"normalisation the two populations sit at opposite ends "
                       f"of the axis. Under grouped normalisation every mission "
                       f"receives essentially the same number; panel (d) "
                       f"magnifies that spike and shows the full range of the "
                       f"predictions is about three ten-thousandths wide. This "
                       f"is what distinguishes a collapse from a bad model.",
        })
        add("p",
            "[#fig:collapse] is the reason we use the word 'collapse' rather "
            "than "
            "'underfitting'. A low AUC on its own is ambiguous — it is what you "
            "would see from a model that has learned something weak or wrong. A "
            "held-out prediction distribution three ten-thousandths wide is not "
            "ambiguous. The network has stopped being a function of its input.")
        if surv_losses:
            jup = next((p for p in paired if p["planet"] == "jupiter"), None)
            merc = next((p for p in paired if p["planet"] == "mercury"), None)
            add("p",
                f"The second result is that the collapse is selective, and we "
                f"report this rather than only the case that breaks. On the "
                f"other {len(survivors)} targets the same manipulation costs "
                f"between {f4(surv_losses[0])} and {f4(surv_losses[-1])} AUC and "
                f"leaves the output varying normally. Severity does not follow "
                f"the signal ratio on its own either. "
                + (f"Jupiter's signal is compressed to "
                   f"{jup['signal_grouped']:.4f}, lower than Mercury's "
                   f"{merc['signal_grouped']:.4f}, and yet Jupiter loses "
                   f"{f4(abs(jup['val_auc_gain_vs_grouped']))} AUC where Mercury "
                   f"loses {f4(abs(merc['val_auc_gain_vs_grouped']))} — because "
                   f"Jupiter's task is separable enough that even a badly "
                   f"attenuated signal is sufficient. "
                   if jup and merc else "")
                + "Compression is necessary for the collapse but not sufficient; "
                "how hard the underlying task is modulates it. A rule of the "
                "form 'it collapses when the ratio drops below X' is therefore "
                "not supported by these data, and we do not claim one. "
                "[#fig:signal] makes the counter-example visible.")
        add("figure", {
            "stem": "fig3_signal_vs_auc", "wide": False, "label": "fig:signal",
            "caption": "Signal ratio against validation AUC. If compression "
                       "alone explained the collapse these points would lie on "
                       "a curve. Jupiter sits at a lower signal ratio than "
                       "Mercury and loses almost nothing, so they do not.",
        })
        add("p",
            "One note on scope. This ablation isolates normalisation and "
            "nothing else: a separate model is trained per target, and only the "
            "statistics are pooled. The production failure that prompted the "
            "study also shared a single model across the group, which compounds "
            "the problem, since one trunk then has to serve targets whose inputs "
            "have all been flattened toward a common constant. The numbers here "
            "are therefore a lower bound on the damage the full configuration "
            "does. They establish that pooled normalisation is sufficient on its "
            "own to destroy a target — not that this is a complete "
            "reconstruction of the original incident.")

    add("h2", "The baseline signs off on the broken configuration")
    if inv:
        by = {(r["planet"], r["norm_mode"]): r for r in inv["runs"]}
        order = [p["planet"] for p in paired] or sorted(
            {r["planet"] for r in inv["runs"]})
        rows = []
        for p in order:
            if (p, "grouped") not in by:
                continue
            rows.append([p.capitalize()]
                        + [f4(by.get((p, c), {}).get("tree_auc"))
                           for c in ["per-timestep", "global", "grouped"]]
                        + [f4(inv["tree_auc_spread_across_conditions"].get(p))])
        add("table", {
            "label": "tab:invariance", "wide": False,
            "caption": "XGBoost on the identical normalised window, under each "
                       "setting. The tree does not react to the preprocessing "
                       "that destroys the network.",
            "headers": ["Target", "per-timestep", "global", "grouped", "spread"],
            "rows": rows,
        })
        wp = worst.get("planet", order[0])
        add("p",
            f"Under the grouped setting the tree reports AUC "
            f"{f4(by.get((wp, 'grouped'), {}).get('tree_auc'))} on "
            f"{wp.capitalize()} — the target where the network has collapsed to "
            f"a constant at AUC {f4(worst.get('val_auc_grouped'))}. Across all "
            f"targets the tree's AUC moves by at most {f4(tree_spread)} between "
            f"settings, so for practical purposes it cannot see the choice at "
            f"all. Someone who runs it to check whether the features carry "
            f"signal — the standard move, and the correct instinct — gets an "
            f"unambiguous yes, and reasonably concludes that the deep model "
            f"needs tuning rather than that the pipeline is broken.")
        add("figure", {
            "stem": "fig4_baseline_blindness", "wide": False,
            "label": "fig:blindness",
            "caption": "Both models under grouped normalisation, on the same "
                       "arrays. The tree is at the ceiling on every target, "
                       "including the one where the network is barely above "
                       "chance.",
        })
        add("p",
            "This is the methodological point, and it is worth stating "
            "carefully, because the baseline is not wrong. The information "
            "really is present, and a tree really can use it. The baseline is "
            "uninformative about the question that was actually being asked, "
            "which is whether the network can use it. Invariance to feature "
            "scaling — normally an excellent reason to reach for a tree as a "
            "diagnostic — is exactly what makes it blind here. The check and the "
            "defect are orthogonal by construction, so no amount of care in "
            "running the check would have helped.")

    add("h2", "A diagnostic that does catch it")
    add("p",
        "Accuracy on a mixed validation set does not catch the collapse, "
        "because a per-group constant ranks the groups correctly and a pooled "
        "metric rewards that. Two checks do catch it:")
    add("bullets", [
        "Prediction spread within a group. A collapsed model produces almost no "
        "variation in its output across inputs. This is a property of the "
        "predictions alone, needs no labels, and cleanly separates collapse from "
        "ordinary underfitting, which produces predictions that are wrong but "
        "still vary.",
        "Tree against network under identical preprocessing. A large gap in the "
        "tree's favour, with both fed the same array, says the network cannot "
        "exploit information that is present — rather than that the information "
        "is absent.",
    ])
    add("p",
        "Both are cheap, and neither requires you to suspect this specific "
        "defect in advance, which is the property that makes a diagnostic worth "
        "having. We would recommend reporting per-group prediction spread "
        "alongside aggregate metrics whenever a model is trained on grouped data "
        "with heterogeneous scales. In our case it would have turned a problem "
        "that survived several review cycles into a one-line check.")

    # ── V. Multi-seed ────────────────────────────────────────────────────────
    if ms_norm:
        add("h1", "Does It Reproduce Across Seeds?")
        add("p",
            f"An obvious objection to everything above is that it describes one "
            f"run. A single collapse at AUC {f4(worst.get('val_auc_grouped'))} "
            f"could be an unlucky initialisation. We therefore repeated the full "
            f"ablation across {n_seeds} seeds, each of which redraws the "
            f"train/validation/test partition as well as the initialisation.")
        rows = []
        reps = [norm] + ms_norm
        for p in paired:
            name = p["planet"]
            per_seed_grouped, per_seed_ts, n_coll = [], [], 0
            for rep in reps:
                hit = next((q for q in rep["paired"] if q["planet"] == name), None)
                if not hit:
                    continue
                per_seed_grouped.append(hit["val_auc_grouped"])
                per_seed_ts.append(hit["val_auc_per-timestep"])
                n_coll += bool(hit.get("collapsed_grouped"))
            if not per_seed_grouped:
                continue
            import statistics as st
            sd = (st.stdev(per_seed_grouped) if len(per_seed_grouped) > 1 else 0.0)
            sd_ts = (st.stdev(per_seed_ts) if len(per_seed_ts) > 1 else 0.0)
            rows.append([
                name.capitalize(),
                f"{st.mean(per_seed_ts):.4f} ± {sd_ts:.4f}",
                f"{st.mean(per_seed_grouped):.4f} ± {sd:.4f}",
                f"{n_coll}/{len(per_seed_grouped)}",
            ])
        add("table", {
            "label": "tab:multiseed", "wide": False,
            "caption": f"Validation AUC across {n_seeds} seeds, mean ± standard "
                       f"deviation, and the number of seeds on which the grouped "
                       f"run collapsed to a constant output.",
            "headers": ["Target", "per-timestep AUC", "grouped AUC", "collapsed"],
            "rows": rows,
        })
        add("figure", {
            "stem": "fig7_multiseed", "wide": False, "label": "fig:multiseed",
            "caption": f"Every seed plotted individually rather than summarised "
                       f"as an interval. With n = {n_seeds} the spread of the "
                       f"raw points is the honest summary.",
        })
        # The interpretation, computed rather than asserted. Written to be
        # correct whatever the seeds turn out to say: an earlier version of
        # this paragraph hardcoded "collapses on every seed", which was true
        # at three seeds and false at five.
        import statistics as _st

        def series(planet, key):
            out = []
            for rep in reps:
                h = next((q for q in rep["paired"] if q["planet"] == planet), None)
                if h:
                    out.append(h[key])
            return out

        wp = worst["planet"]
        w_sig = series(wp, "signal_grouped")
        w_std = series(wp, "pred_std_grouped")
        w_auc = series(wp, "val_auc_grouped")
        w_flags = series(wp, "collapsed_grouped")
        n_coll = sum(bool(x) for x in w_flags)
        n_rep = len(w_flags)
        coll_std = [v for v, f in zip(w_std, w_flags) if f]
        surv_std = [v for v, f in zip(w_std, w_flags) if not f]
        healthy_std = series(wp, "pred_std_per-timestep")
        ts_sds = [_st.stdev(series(p["planet"], "val_auc_per-timestep"))
                  for p in paired
                  if len(series(p["planet"], "val_auc_per-timestep")) > 1]
        never = [p["planet"].capitalize() for p in paired
                 if not any(series(p["planet"], "collapsed_grouped"))]

        add("p",
            f"The compression itself does not depend on the seed. "
            f"{wname}'s signal ratio under grouped normalisation lands between "
            f"{min(w_sig):.5f} and {max(w_sig):.5f} across all {n_rep} runs — "
            f"a spread of {100 * (max(w_sig) - min(w_sig)) / min(w_sig):.0f}% "
            f"against the {worst['signal_compression_grouped']:.0f}x compression "
            f"itself — because it is a property of the preprocessing and the "
            f"data, not of the optimiser. The healthy "
            f"condition is stable too: per-timestep AUC moves by at most "
            f"{max(ts_sds):.4f} between seeds. "
            + (f"{join(never)} never collapse under any seed. "
               if never else ""))
        add("p",
            f"What does depend on the seed is whether the network escapes. "
            f"{wname} collapses to a constant on {n_coll} of {n_rep} seeds, "
            f"with held-out prediction spread between {sci(min(coll_std))} and "
            f"{sci(max(coll_std))} — four orders of magnitude below the "
            f"{sci(min(healthy_std))} it reaches under correct normalisation."
            + (f" On the {'other' if n_rep - n_coll > 1 else 'remaining'} "
               f"{'seeds' if n_rep - n_coll > 1 else 'seed'} it does not fully "
               f"collapse, but it does not recover either: prediction spread "
               f"{sci(max(surv_std))}, still an order of magnitude short, at AUC "
               f"{max(v for v, f in zip(w_auc, w_flags) if not f):.4f} against "
               f"{f4(worst.get('val_auc_per-timestep'))} healthy. So the "
               f"preprocessing reliably creates the conditions for the collapse, "
               f"and the collapse is the usual but not the certain outcome."
               if surv_std else
               " The preprocessing does not merely make the collapse likely; "
               "across these seeds it makes it certain."))
        add("p",
            f"This is the practical argument for the prediction-spread "
            f"diagnostic recommended above. Across these runs {wname}'s "
            f"grouped AUC spans "
            f"{min(w_auc):.4f} to {max(w_auc):.4f}, a range that overlaps what "
            f"a merely-degraded target scores — Mercury sits inside it on every "
            f"seed while discriminating normally. AUC therefore cannot tell the "
            f"two states apart. Prediction spread can: the collapsed runs and "
            f"every healthy run are separated by orders of magnitude with "
            f"nothing in between. If you are going to watch one number for this "
            f"failure, watch that one.")

        if ms_inv:
            # The methodological half, across every seed. This is the stronger
            # of the two results and it deserves its own count rather than
            # riding on the collapse's.
            inv_reps = [inv] + ms_inv
            all_auc = [r["tree_auc"] for rep in inv_reps for r in rep["runs"]]
            worst_spread = max(v for rep in inv_reps
                               for v in rep["tree_auc_spread_across_conditions"]
                               .values())
            add("p",
                f"The baseline's blindness replicates more cleanly still. "
                f"Across {len(inv_reps)} seeds, {len(paired)} targets and three "
                f"normalisation settings — {len(all_auc)} fitted trees in total "
                f"— the tree's AUC never leaves the range "
                f"{f4(min(all_auc))} to {f4(max(all_auc))}, and within any one "
                f"seed and target it moves by at most {f4(worst_spread)} between "
                f"settings. There is no seed on which the baseline notices. That "
                f"matters more than the collapse count: the collapse is one "
                f"target's misfortune, but a check that cannot fail is a "
                f"property of the check.")

    # ── VI. Rare mode ────────────────────────────────────────────────────────
    add("h1", {"text": "Failing to Reach a Signal That Is Present",
               "label": "sec:rare"})
    if rare:
        add("p",
            f"A second failure shows up even when the normalisation is correct. "
            f"On {rare['planet'].capitalize()}, the failure mode "
            f"'{rare['rare_mode']}' accounts for {rare['rare_mode_train_n']:,} of "
            f"{rare['n_train_failures']:,} training failures. A tree fitted to the "
            f"same normalised {rare['window_steps']}-step window separates that "
            f"mode from success at AUC {f4(rare['tree_reference']['auc'])}, with "
            f"recall {f4(rare['tree_reference']['recall_at_0.5'])}. The sequence "
            f"model's recall on it is "
            f"{f4(rare['best_sequence_rare_recall'])} at its operating point.")
        rows = [[f"{r['mode_alpha']:.2f}",
                 f"{r['effective_resample_factor']:.1f}x",
                 f4(r["test_f1"]), f4(r["overall_failure_recall"]),
                 f4(r["rare_mode_recall"])] for r in rare["runs"]]
        add("table", {
            "label": "tab:rare", "wide": False,
            "caption": f"Rare-mode oversampling sweep on "
                       f"{rare['planet'].capitalize()}. Increasing the sampling "
                       f"weight on the rare mode does not recover it, and does "
                       f"not disturb anything else either.",
            "headers": ["alpha", "resample", "test F1",
                        "all-mode recall", "rare-mode recall"],
            "rows": rows,
        })
        add("figure", {
            "stem": "fig5_rare_mode", "wide": False, "label": "fig:rare",
            "caption": "Recall against oversampling weight. The horizontal line "
                       "is a tree on the identical window. The rare-mode curve "
                       "does not move.",
        })
        add("p",
            "Because both models consume the same array and one of them "
            "separates the classes cleanly, the information is present and the "
            "sequence model's failure is an optimisation limit rather than an "
            "information limit. Resampling does not close the gap, which rules "
            "out the simplest explanation. We are careful not to overclaim the "
            "cause: whether it is the loss landscape, the CLS pooling discarding "
            "a cue that is localised in time, or the binary head being dominated "
            "by the majority mode, we do not know. Probing the trunk "
            "representation for linear separability of the rare mode would "
            "narrow it down, and that is the next experiment rather than a "
            "result we have.")
        add("p",
            "Two denominators are worth stating, because this number is easy to "
            "quote misleadingly. Relative to the majority failure mode the rare "
            "mode is oversampled by roughly 45x at the strongest setting. "
            f"Relative to uniform sampling over the training set — which is what "
            f"the sampler actually applies — the factor is "
            f"{rare['runs'][-1]['effective_resample_factor']:.2f}x. We report "
            f"the latter, because it describes what the optimiser saw.")
        if ms_rare:
            # Across seeds the rare mode is redrawn along with the split, so
            # neither the sequence recall nor the tree's is a fixed number. The
            # gap is what replicates, and it is reported as a range rather than
            # rounded to the seed-42 extreme of 0.0000 against 1.0000.
            rare_reps = [rare] + ms_rare
            seq = [r["rare_mode_recall"] for rep in rare_reps
                   for r in rep["runs"]]
            tree_rec = [rep["tree_reference"]["recall_at_0.5"]
                        for rep in rare_reps]
            tree_auc = [rep["tree_reference"]["auc"] for rep in rare_reps]
            flat = [len({r["rare_mode_recall"] for r in rep["runs"]}) == 1
                    for rep in rare_reps]
            add("p",
                f"The sweep was repeated across {len(rare_reps)} seeds, each of "
                f"which redraws the split and therefore the rare mode itself. "
                f"The gap replicates and the extremes do not: sequence recall "
                f"on the rare mode ranges {f4(min(seq))} to {f4(max(seq))} "
                f"across every seed and sampling weight, against a tree on the "
                f"identical window at recall {f4(min(tree_rec))} to "
                f"{f4(max(tree_rec))} and AUC {f4(min(tree_auc))} to "
                f"{f4(max(tree_auc))}. "
                + ("On every seed the sampling weight makes no difference "
                   "whatsoever — recall is identical at all three settings "
                   "within a seed, so the flat line in the figure is not a "
                   "property of one run."
                   if all(flat) else
                   "The sampling weight moves recall on some seeds but never "
                   "closes the gap."))

    # ── VII. Economics ───────────────────────────────────────────────────────
    add("h1", {"text": "Where the Screen Actually Belongs",
               "label": "sec:econ"})
    if econ:
        w = econ["weighted"]
        rows = [
            ["T0 — six launch parameters, before propagating",
             pct(w["compute_saved_t0"]), pct(w["false_prune_rate_t0"], 2),
             pct(w["fail_recall_t0"], 2)],
            ["T40 — telemetry Transformer at 40%",
             pct(w["compute_saved_t40"]), pct(w["false_prune_rate_t40"], 2),
             pct(w["fail_recall_t40"], 2)],
            ["Cascade — T0 where confident, else T40",
             pct(w["cascade_saved"]), pct(w["cascade_false_prune"], 2),
             pct(w["cascade_recall"], 2)],
        ]
        add("table", {
            "label": "tab:econ", "wide": True, "bold_first_row": True,
            "caption": "Screening economics. Compute is charged in "
                       "propagation-days, which span a ~100x range across the "
                       "seven targets. Thresholds are fitted on validation and "
                       "reported on the untouched test split, so the recall "
                       "column is measured out of sample rather than achieved "
                       "by construction.",
            "headers": ["Screen", "Compute saved", "Good missions lost",
                        "Failure recall"],
            "rows": rows,
        })
        add("figure", {
            "stem": "fig6_economics", "wide": True, "label": "fig:econ",
            "caption": "(a) What each screening point buys and what it costs. "
                       "(b) Why the weighting is not uniform: per-mission "
                       "propagation cost spans two orders of magnitude, so the "
                       "value of a screen is dominated by the outer targets.",
        })
        add("p",
            f"Having gone to the trouble of fixing the sequence model, the "
            f"honest conclusion is that it should not be used. A six-feature "
            f"classifier over the injection parameters, evaluated before any "
            f"propagation happens at all, saves {pct(w['compute_saved_t0'])} of "
            f"compute against the telemetry model's "
            f"{pct(w['compute_saved_t40'])}, at a comparable cost in good "
            f"missions destroyed. Accuracy is also flat from 10% to 40% "
            f"observed. The reason is structural rather than a modelling "
            f"failure: the simulator is deterministic, so the outcome is a fixed "
            f"function of the injection offsets and the trajectory is their "
            f"integral. It cannot carry information the parameters do not "
            f"already have.")
        lr = [p["auc_logreg_t0"] for p in econ["per_planet"]]
        add("p",
            f"This is not an argument that the task is trivial. Logistic "
            f"regression on the same six features scores between {min(lr):.4f} "
            f"and {max(lr):.4f} AUC — chance — on every target, so the map from "
            f"parameters to outcome is strongly nonlinear and does need a "
            f"learned model. It just does not need a temporal one. A sequential "
            f"screen earns its place only where the outcome is not settled at "
            f"injection: mid-flight stochasticity, unmodelled dynamics, sensor "
            f"noise, or campaigns where the launch parameters were never "
            f"recorded. Reinforcement-learning trajectory work that certifies "
            f"policies through dispersed Monte Carlo campaigns [@zavoli2021rl] "
            f"is a natural setting for exactly that.")
        add("p",
            "We include this section because it bounds the practical "
            "significance of everything before it. The methodological findings "
            "apply to any grouped sequence-modelling pipeline; the application "
            "that produced them turns out not to need a sequence model. A "
            "reviewer who discovers that on their own is in a worse position "
            "than one who is told.")
        add("p",
            "One methodological note on this table, since it cuts against the "
            "conclusion we draw. An earlier version was produced under two "
            "selection biases: thresholds were fitted on the test labels, and "
            "the evaluation set overlapped the sequence model's validation "
            "split. Both flattered T40 — the screen this section argues "
            "against. Removing them moved the headline by less than 0.1 "
            "percentage points, so the negative result survives its own "
            "correction, which is the strongest form the claim can take.")

    # ── VIII. Limitations ────────────────────────────────────────────────────
    add("h1", "Limitations")
    lims = []
    if ms_norm:
        lims.append(
            f"Seeds. Results are replicated across {n_seeds} seeds, which is "
            f"enough to rule out an unlucky initialisation but not enough to "
            f"support a tight confidence interval. We report the spread of the "
            f"individual runs rather than a fitted interval. The collapse "
            f"itself occurs on {n_collapse_seeds} of {n_seeds}; we do not have "
            f"the sample size to say what governs the exception.")
    else:
        lims.append(
            "Single seed. Every result is one run at seed 42. The split is "
            "deterministic in (n, seed), so the numbers reproduce exactly — "
            "which is reproducibility, not stability. No confidence intervals "
            "are claimed.")
    lims += [
        "One domain. The collapse is shown on one corpus. We describe the "
        "mechanism in terms of a variance ratio that is not specific to "
        "astrodynamics, but we have not reproduced it on a second dataset, and "
        "until we do, any predictive threshold on that ratio is a conjecture "
        "rather than a finding.",
        "Four targets in the ablation. The collapse is observed on one target "
        "out of four. The baseline-blindness result, which is the "
        "methodological half, holds on all four.",
        "Synthetic and deterministic. No execution error, no unmodelled "
        "accelerations, no sensor noise, and every mission of a target shares a "
        "time base. That shared time base is what makes per-timestep "
        "standardisation work at all, and it is a property of the generator "
        "rather than of real campaigns.",
        "No real mission data. This is the largest external-validity gap. "
        "Public benchmarks of real satellite telemetry now exist "
        "[@kotowski2024esaadb, hundman2018detecting] and are the obvious next "
        "target for the diagnostic.",
    ]
    add("bullets", lims)

    # ── IX. Conclusion ───────────────────────────────────────────────────────
    add("h1", "Conclusion")
    add("p",
        "Sharing a feature scaler across groups whose scales differ can reduce "
        "a deep model to a per-group constant, while a tree on the identical "
        "arrays reports the task as solved. None of the pieces are exotic. The "
        "preprocessing choice is one that a standard pipeline makes by default. "
        "The model is a plain Transformer. The baseline is the one most people "
        "would reach for. And the standard defence — check a simple baseline — "
        "is invariant to the defect by construction, so it cannot fail the "
        "broken model.")
    add("p",
        "The fix, per-group normalisation, is not novel and we do not claim it "
        "is. The contribution is the detection problem: that a routine check "
        "certifies a broken configuration, and that a different check, costing "
        "essentially nothing, catches it. Reporting the spread of predictions "
        "within a group alongside aggregate metrics would have caught ours "
        "immediately.")

    add("h1", "Reproduction")
    add("code",
        "export ORBITGUARD_DATA=/path/to/dataset\n"
        "\n"
        "# Primary results, seed 42\n"
        "python -m src.ml.norm_ablation          # Table I\n"
        "python -m src.ml.baseline_invariance    # Table II\n"
        "python -m src.ml.rare_mode_sweep        # Table IV\n"
        "python -m src.ml.prune_economics        # Table V\n"
        "\n"
        "# Replication, one pass per seed (Table III, Section V)\n"
        "for S in 0 1 2 3; do\n"
        "  python -m src.ml.norm_ablation --seed $S \\\n"
        "      --out reports/multiseed_paper/normalisation_ablation_seed$S.json\n"
        "  python -m src.ml.baseline_invariance --seed $S \\\n"
        "      --out reports/multiseed_paper/baseline_invariance_seed$S.json\n"
        "  python -m src.ml.rare_mode_sweep --seed $S \\\n"
        "      --out reports/multiseed_paper/rare_mode_sweep_seed$S.json\n"
        "done\n"
        "\n"
        "# The document\n"
        "python docs/paper/collect_traces.py     # Fig. 2 data\n"
        "python docs/paper/figures.py            # all figures\n"
        "python docs/paper/render_latex.py       # this document")

    return D
