# Reviewer Revision Audit

Branch: `codex/revise-collapse-diagnostic`

Base: `origin/main` at `439e273` (fetched 2026-10-13)

Purpose: address reviewer requests on diagnostic scope, mission assurance,
operational monitoring, threshold provenance, prior work, generalisation, and
uncertainty without presenting unrun experiments as results.

## Checklist

- [x] Fetch latest `origin/main` and create an isolated branch/worktree.
- [x] Preserve the pre-existing dirty checkout; do not incorporate its files.
- [x] Inventory manuscript, experiment scripts, and machine-readable reports.
- [x] Verify collapse-definition and threshold provenance from code/history.
- [x] Verify whether C-MAPSS and broader collapse-severity artifacts exist.
- [x] Add the requested related-work comparison table and literature.
- [x] Narrow the tree-baseline claim to this scale-invariant baseline and this
  scaling failure.
- [x] Distinguish label-free inference-time statistics from development-time
  threshold calibration and performance evaluation.
- [x] State threshold scope, selection chronology, and transfer limits.
- [x] Add mission-assurance consequences and a concrete operational pipeline.
- [x] Separate demonstrated results from proposed operational implications.
- [x] Strengthen uncertainty reporting using only available artifacts.
- [x] Keep full and anonymous manuscripts synchronized.
- [x] Compile both manuscripts and run repository tests/checks.
- [x] Cross-check claims against JSON artifacts and scripts.
- [x] Commit and push the branch.

## Evidence and decisions

### Repository state

- The original checkout was on `codex/fix-baseline-split-cadence` with modified
  and untracked experiment outputs. A clean managed worktree was therefore
  created from the fetched remote default branch.
- Paper sources are `eaai/manuscript.tex` and
  `eaai/manuscript_anonymous.tex`; their scientific text is intended to match.

### Collapse definition and threshold

- `src/ml/norm_ablation.py` computes prediction spread as the standard
  deviation of `P(fail)` on the held-out split and assigns
  `collapsed = pred_std < 1e-3`.
- The `1e-3` rule first appears in commit `5740ccc`; the multi-seed replication
  was added later in `c145cc9`. It was therefore fixed before the additional
  multi-seed runs, but after the original incident/single-run analysis.
- The threshold was not optimized against test labels or test AUC. Indeed, the
  statistic itself is label-free. However, it is a heuristic development rule,
  not a cross-domain calibrated operating threshold. Labels are still required
  to estimate false-alarm/miss rates and to calibrate a deployable threshold.
- The reported state assignment is exactly the `1e-3` spread rule. Four Venus
  grouped runs fall below it; one Venus grouped run (seed 3, spread about
  `3.64e-2`) does not. All other reported runs are far above it.

### Available and unavailable experiments

- The repository contains four ablation targets (Venus, Mars, Mercury,
  Jupiter), five seeds (seed 42 plus seeds 0--3), and three normalization
  conditions.
- An LSTM control exists in `reports/arch_ablation/`, but it tests the ordinary
  screening task with the working preprocessing. It does **not** test grouped
  normalization and therefore does not answer whether collapse is specific to
  the Transformer configuration.
- No C-MAPSS artifact, script, or manuscript result is present in the latest
  repository. No C-MAPSS transfer claim will be added without auditable output.
- No experiment spans near-constant predictions, graded compression, and
  broader degraded states with detector false-alarm/miss counts. This remains
  future work rather than a demonstrated result.
- `src/ml/multi_seed_economics.py` can quantify multi-seed uncertainty for the
  T0 screen. It does not evaluate T40 or the cascade, which remain single-run
  estimates unless further experiments are supplied.
- The T0 five-split run completed against the local merged dataset. Its artifact
  is `reports/prune_economics_multiseed.json`: compute saved
  `0.6450 +/- 0.0061`, false-prune rate `0.01237 +/- 0.00241`, and failure
  recall `0.98992 +/- 0.00180` (mean +/- population standard deviation over
  split seeds 0--4). These are resplits of one corpus, not domain-level
  confidence intervals. T40 and cascade remain single-seed results.

### Claim policy

- “Demonstrated” is reserved for results traceable to committed artifacts.
- “Operational implication” and “proposed pipeline” identify extrapolations.
- Tree claims are limited to the tested XGBoost baseline on the identical
  transformed arrays; tree models in general may diagnose other preprocessing
  failures.

## Validation log

Commands and outcomes will be recorded here as they are completed.

- `git fetch origin --prune`: advanced `origin/main` from `177b397` to
  `439e273`.
- `python -m src.ml.multi_seed_economics --out
  reports/prune_economics_multiseed.json` with `ORBITGUARD_DATA` pointing to
  the local merged corpus: passed for seeds 0--4.
- `eaai/compile.ps1`, followed by final targeted LaTeX passes for both
  manuscripts: compiled successfully. Final logs contain no oversized floats,
  undefined citations/references, emergency stops, or fatal errors.
- Both final PDFs were rendered to PNG. Full-document contact sheets and direct
  inspection of the comparison table, mission-assurance section, screening
  economics, and limitations showed no clipping, overlap, or illegible content.
- `python -m py_compile src/ml/norm_ablation.py
  src/ml/multi_seed_economics.py`: passed.
- Economics JSON schema and manuscript rounding were asserted against the
  generated artifact: passed.
- `git diff --check`: passed.
- `python -m pytest -q`: collection is blocked by pre-existing helper functions
  named `test_indices(n, ...)`, which pytest treats as tests requiring an `n`
  fixture. This revision does not alter those files.
- `python -u test_api.py --quick`: health, system metadata, target coverage,
  thresholds, and mission construction passed. Dataset/model-dependent checks
  failed because the clean worktree does not contain the ignored model weights
  and defaults to the reference Linux data path; this is unrelated to the
  manuscript and diagnostic edits. The declared `httpx==0.28.1` dependency was
  installed in the active environment before this run.
