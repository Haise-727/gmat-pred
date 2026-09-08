# Notes on the draft

Editorial commentary on the paper. The paper states claims; this file states how
much each one is worth, what is still missing, and where a reviewer will push.
Read this before sending the draft to anyone.

## What is in this directory

| File | What it is |
|---|---|
| `content.py` | **The paper.** Prose and tables, with every number read from a `reports/*.json` artifact. |
| `render_latex.py` | → `orbitguard_ieee.tex`, IEEEtran two-column. The submission copy. |
| `build_paper.py` | → `OrbitGuard_paper_draft.docx`, two-column Word. The reading copy. |
| `figures.py` | → `figures/*.pdf` and `*.png`. Also generated from the artifacts. |
| `collect_traces.py` | Replays the ablation checkpoints to produce the raw predictions behind Fig. 2. |
| `references.bib` | 32 entries. |
| `IEEEtran.cls`, `.bst` | Vendored so the source compiles anywhere, including Overleaf. |

Nothing here is hand-edited output. **Do not edit the `.tex`, the `.docx` or a
number in a figure** — edit `content.py`, or re-run the experiment that produced
the artifact. This is not pedantry: the project previously had three model
generations of contradictory figures scattered across `docs/`, and making the
prose a function of the measurements is the only fix that held.

To rebuild everything:

```bash
python docs/paper/figures.py
python docs/paper/render_latex.py && python docs/paper/build_paper.py
cd docs/paper && pdflatex orbitguard_ieee && bibtex orbitguard_ieee \
    && pdflatex orbitguard_ieee && pdflatex orbitguard_ieee
```

## Claim → evidence map

| Claim in the paper | Backed by | Confidence |
|---|---|---|
| Grouped normalisation collapses the network to a constant | `reports/normalisation_ablation.json` + `reports/multiseed_paper/` | **Measured, multi-seed.** Controlled: same architecture and split; only pooling differs. |
| Timestep pooling is survivable, group pooling is not | same | **Measured.** This decomposition is new — the original incident report blamed scaling in general. |
| A tree is invariant to the normalisation that kills the network | `reports/baseline_invariance.json` | **Measured.** Tree AUC moves ≤0.0002 across all three conditions, on every target. |
| Prediction spread is the right diagnostic, not AUC | the multi-seed run | **Measured.** The collapsed target's AUC moves between seeds; its prediction spread does not change order of magnitude. |
| The sequence model cannot reach a rare mode a tree separates | `reports/rare_mode_sweep.json` | **Measured** on one target, one rare mode. |
| Input-space screening dominates telemetry screening | `reports/prune_economics.json` | **Measured**, and re-verified after removing two selection biases. |
| Logistic regression on the six features is at chance | `auc_logreg_t0` in the economics artifact | **Measured.** |
| Architecture description (d_model 128, 8 heads, 4 layers, Pre-LN, CLS) | `src/ml/model.py` | **Verified against source.** |
| 70,000 missions / 7 targets / 10,000 each | `data/per_planet/*.npz`, `planet_config.py` | **Verified.** |

## Two things that changed from the original framing

Both weaken the original claim, and both are stated in the paper rather than
left for a reviewer to find.

**1. The within-planet comparison does not reproduce the collapse.**
`RESEARCH_PROPOSAL.md` originally described C1 as "sharing one feature scaler
across heterogeneous groups", supported by a table comparing a global
RobustScaler against per-timestep z-scoring *within a single planet* (Mars val
AUC 0.939 → 0.998). That table was never reproducible — no script produced it —
and the rebuilt experiment contradicts it: pooling one target's own timesteps
costs at most a few thousandths of AUC. All four targets survive it. The
collapse requires pooling across *targets*. This is a sharper and better claim
than the original, but it is a different one.

**2. The collapse is selective — one target in four.** Only Venus degenerates to
a constant. Mercury, Mars and Jupiter lose between 0.0003 and 0.09 AUC and keep
discriminating. Severity does not track the compression ratio cleanly either:
Jupiter's grouped signal is *lower* than Mercury's yet Jupiter loses almost
nothing, because its task is separable enough to survive heavy attenuation. So
compression is necessary but not sufficient, and the "collapse when the ratio
exceeds X" rule the proposal hoped for is **not supported**. The paper says so.

**Scope caveat, in the paper.** The ablation isolates normalisation alone — one
model per target, only the statistics pooled. The production incident also
shared a single model across the group, which compounds the damage. The measured
numbers are a lower bound on the original failure, not a reproduction of it.

## Resolved since the first draft

- **Related work.** Was a stub, and was the single largest gap. Now written, at
  five subsections, against 32 references: normalisation and what it assumes,
  shortcut learning and misleading aggregate metrics, trees as baselines,
  rare-class optimisation limits, and learned screening in astrodynamics.
- **Space/astrodynamics positioning.** The paper previously cited no aerospace
  literature at all, which for a paper set in astrodynamics is a reviewer's
  first question. 15 verified space references now anchor it — the ESA/Izzo
  guidance-and-control line, GMAT's own V&V paper, the TESS Monte Carlo
  dispersion campaign as the cost motivation, JPL's LSTM telemetry work and the
  ESA anomaly benchmark, and conjunction screening as the nearest prior art.
- **Single seed.** Was "no defence, fix it". The full ablation now runs across
  multiple seeds and Section V reports it. The collapse reproduces on every
  seed; the survivors never collapse on any.
- **IEEE format and a compiled PDF.** The draft was a single-column Word file.
  It is now a two-column IEEEtran paper with a real bibliography, plus seven
  figures, and the Word version is generated from the same source.

## Still not evidenced

- **One dataset.** The mechanism is described in terms of a variance ratio that
  is not astrodynamics-specific, but it has been shown on one corpus. The paper
  says this. A methods venue will still want a second demonstration — ideally a
  public grouped time-series dataset with heterogeneous group scales. The ESA
  anomaly benchmark (`kotowski2024esaadb`) is now cited as the obvious target.
- **Four targets in the ablation, one collapse event.** Reviewer 2 will say "you
  found a bug on Venus". The answers are (a) the ablation is controlled and the
  mechanism is measured rather than inferred, now across seeds, and (b) the
  baseline-blindness result holds on all four targets, not only the one that
  collapsed — that half is not anecdotal.
- **The rare-mode cause.** Section VI establishes that the failure is an
  optimisation limit rather than an information limit, and stops there. It does
  not say *why*. The cheapest next probe is linear separability of the rare mode
  in the trunk representation: separable there ⇒ the defect is in the head.
- **No real mission data.** Largest external-validity gap.

## A number that changes depending on the denominator

The ledger and `train_assist.py`'s docstring say the rare mode was oversampled
"up to 45x" without recovering it. The measured sweep reports **19.23x** at
`mode_alpha=1.0`. Both are right under different denominators: 45x is the ratio
to the *majority* failure mode (4113/91), 19.2x is the factor relative to
*uniform* sampling over the training set, which is what the sampler actually
applies. The paper reports the latter and labels it, because it is the quantity
that describes what the optimiser saw. If you quote 45x anywhere, say against
what.

The conclusion is unchanged and if anything stronger than the prose claimed:
recall on the rare mode is exactly 0.0000 at every alpha, while a tree on the
identical window reaches AUC 1.0000 and recall 1.0000.

## Where a reviewer will push

1. **"Isn't this just a bug you had?"** The defence is the controlled ablation
   plus the decomposition — it is a reproducible property of the preprocessing,
   not an incident. Lead with Table I and Fig. 2, not with the story.
2. **"Why would anyone pool a scaler across groups?"** Because it is the default
   when you fit one `RobustScaler` on a concatenated training set, which is what
   almost every tutorial pipeline does. Section III-C says this explicitly; the
   finding is only interesting if the mistake is natural.
3. **"Your fix is just per-group normalisation, which is known."** True, and the
   paper does not claim the fix is novel — the conclusion says so in as many
   words. The contribution is the *detection* problem: that the standard sanity
   check certifies the broken configuration.
4. **"Single seed."** Answered. See Section V.
5. **"Section VII says the whole application doesn't need the model."**
   Deliberate. It bounds the practical claim and pre-empts the obvious
   objection. A reviewer who finds it themselves is much worse than one who is
   told.

## Venue

Written for a **methods / negative-results** audience — the collapse and the
detection failure are the product, and the astrodynamics is the setting. Do not
send this to an aerospace venue: Section VII concludes their application does
not need the method, and Sections IV–VI are about optimisation pathology.

The aerospace paper is a *different* paper (the economics plus the dataset), and
it needs WP1 — regenerating data with mid-flight stochasticity — before it has a
positive result to report rather than a negative one.

## Open decisions for you

- **Affiliation** is a placeholder in `content.py` (`AFFILIATION`).
- **Authorship** — `rohitmichael-alt` has 15 commits in the repository's history
  and the earlier dataset generation. The author list in `content.py` currently
  names both; confirm it before circulating.
- **Dataset release.** C4 in the proposal offers the corpus as a contribution.
  The mission tables are ~71 GB; a release needs a hosting plan and probably a
  downsampled public subset. The per-planet `.npz` extracts (~70 MB each) are a
  reasonable candidate.
- Whether to keep Section VII at all, or cut it and make the paper purely
  methodological. The current draft keeps it, on the grounds that it is honest
  and pre-empts an obvious objection — but it does dilute the focus.
