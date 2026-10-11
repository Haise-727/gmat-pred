"""
Runs for the prediction-spread diagnostic.

The normalisation ablation (norm_ablation.py) stores the spread of P(fail) on the
test split only. To fix a threshold on validation data and then check it on the
test split, both sets of predictions have to be kept. This script repeats the
ablation, same models and same training code, and saves P(fail) for the
validation and the test missions of every run.

It writes to its own files and does not touch reports/normalisation_ablation.json.

    python -m src.ml.diagnostic_runs                     # 4 targets x 3 modes x 5 seeds
    python -m src.ml.diagnostic_runs --seeds 42 --planets venus --modes grouped
"""

from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import torch

from src.ml.dataset import FEATURE_COLS
from src.ml.model import TrajectoryTransformer
from src.ml.norm_ablation import (
    CONDITIONS, DEFAULT_PLANETS, group_of, grouped_stats, signal_ratio,
)
from src.ml.per_planet_train import apply_timestep_norm, fit_norm_stats, predict, train_planet
from src.ml.planet_config import N_FAILURE_CLASSES, OPERATING_FRAC
from src.ml.splits import train_val_test

ROOT = Path(__file__).resolve().parents[2]
SEEDS = [42, 0, 1, 2, 3]          # the five seeds the paper already reports


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--planets", nargs="+", default=DEFAULT_PLANETS)
    ap.add_argument("--modes", nargs="+", default=CONDITIONS)
    ap.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--data-dir", default="data/per_planet")
    ap.add_argument("--out", default="reports/diagnostic_runs")
    ap.add_argument("--work-root", default="models/_diag_runs")
    args = ap.parse_args()

    data_dir = ROOT / args.data_dir
    out = ROOT / args.out
    out.parent.mkdir(exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    runs, preds = [], {}
    meta_path, npz_path = out.with_suffix(".json"), out.with_suffix(".npz")
    if meta_path.exists() and npz_path.exists():          # resume
        runs = json.loads(meta_path.read_text())["runs"]
        preds = dict(np.load(npz_path))
    done = {(r["planet"], r["norm_mode"], r["seed"]) for r in runs}

    for seed in args.seeds:
        for planet in args.planets:
            z = np.load(data_dir / f"{planet}.npz")
            X, y, lengths = z["X"], z["y"], z["lengths"]
            tr, va, te = train_val_test(len(y), seed)
            preds[f"{planet}__s{seed}__y_val"] = y[va]
            preds[f"{planet}__s{seed}__y_test"] = y[te]
            for mode in args.modes:
                if (planet, mode, seed) in done:
                    continue
                if mode == "grouped":
                    mu, sd = grouped_stats(planet, group_of(planet), data_dir, seed, X.shape[1])
                    injected, train_mode = (mu, sd), "global"
                else:
                    mu, sd = fit_norm_stats(X[tr], lengths[tr], mode)
                    injected, train_mode = None, mode
                t0 = time.time()
                work = ROOT / args.work_root / f"{planet}_{mode}_s{seed}"
                meta = train_planet(planet, data_dir, work, epochs=args.epochs, seed=seed,
                                    device=device, norm_mode=train_mode, norm_stats=injected)

                Xn = torch.from_numpy(apply_timestep_norm(X, mu, sd))
                model = TrajectoryTransformer(
                    input_dim=len(FEATURE_COLS), output_dim=1, task="binary",
                    aux_dim=meta.get("aux_dim", N_FAILURE_CLASSES)).to(device)
                model.load_state_dict(torch.load(work / "model.pt", map_location=device, weights_only=True))
                model.eval()
                lt = torch.from_numpy(lengths)
                pf_va = 1.0 - predict(model, Xn, lt, va, OPERATING_FRAC, device)[0]
                pf_te = 1.0 - predict(model, Xn, lt, te, OPERATING_FRAC, device)[0]
                key = f"{planet}__{mode}__s{seed}"
                preds[key + "__val"], preds[key + "__test"] = pf_va, pf_te

                runs.append(dict(planet=planet, norm_mode=mode, seed=seed,
                                 signal_ratio=round(signal_ratio(X, lengths, mu, sd), 8),
                                 val_auc=meta["best_val_auc"],
                                 test_f1=meta["test_at_operating_point"]["f1"],
                                 seconds=round(time.time() - t0, 1)))
                print(f"  seed {seed:>2} {planet:8} {mode:13} val_auc {runs[-1]['val_auc']:.4f} "
                      f"test_f1 {runs[-1]['test_f1']:.4f}  std(test) {pf_te.std():.2e}  "
                      f"({runs[-1]['seconds']}s)", flush=True)
                meta_path.write_text(json.dumps(dict(
                    description="Re-run of the normalisation ablation that keeps validation and "
                                "test P(fail) for every run, for the prediction-spread diagnostic.",
                    epochs=args.epochs, operating_frac=OPERATING_FRAC, runs=runs), indent=1))
                np.savez_compressed(npz_path, **preds)
                del model
                if device.type == "cuda":
                    torch.cuda.empty_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
