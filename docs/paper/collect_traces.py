"""
Recompute held-out predictions from the ablation checkpoints, for the figures.

The ablation artifact (reports/normalisation_ablation.json) records summary
statistics: AUC, F1, and the standard deviation of P(fail). Those are enough for
the tables but not for the figures, because the *shape* of the prediction
distribution is the actual evidence of collapse. A standard deviation of 3e-05
tells you the spread is small; the histogram shows you the network emitting one
number for every mission, which is the claim.

So this script reloads each checkpoint that `src/ml/norm_ablation.py` left in
models/_norm_ablation/, replays the held-out split through it, and writes the raw
P(fail) vectors to a single npz. Figures read that file; nothing re-trains.

Anything the checkpoint dir already knows is read from disk rather than
recomputed, so the traces cannot drift from the run that produced the tables:
the normalisation statistics come from the checkpoint's own norm_stats.npz, and
the split comes from src/ml/splits.py with the same seed.

Usage:
    python docs/paper/collect_traces.py
    python docs/paper/collect_traces.py --work-root models/_norm_ablation
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.ml.dataset import FEATURE_COLS                          # noqa: E402
from src.ml.model import TrajectoryTransformer                   # noqa: E402
from src.ml.per_planet_train import apply_timestep_norm, predict  # noqa: E402
from src.ml.planet_config import (FAILURE_NAMES, N_FAILURE_CLASSES,  # noqa: E402
                                  OPERATING_FRAC)
from src.ml.splits import train_val_test                         # noqa: E402

CONDITIONS = ["per-timestep", "global", "grouped"]


def trace_one(planet: str, mode: str, work_root: Path, data_dir: Path,
              seed: int, device: torch.device) -> dict | None:
    """Held-out P(fail) for one (planet, condition), or None if not trained."""
    ckpt_dir = work_root / f"{planet}_{mode}"
    if not (ckpt_dir / "model.pt").exists():
        print(f"  {planet:9} {mode:13} SKIPPED — no checkpoint at {ckpt_dir}")
        return None

    z = np.load(data_dir / f"{planet}.npz")
    X, lengths, y = z["X"], z["lengths"], z["y"]
    failure_type = z["failure_type"] if "failure_type" in z else None
    _, _, te = train_val_test(len(y), seed)

    # The statistics the checkpoint was actually trained under. Refitting them
    # here would risk a silent mismatch with the run that produced the tables.
    stats = np.load(ckpt_dir / "norm_stats.npz")
    Xn = torch.from_numpy(apply_timestep_norm(X, stats["mu"], stats["sd"]))

    meta = json.loads((ckpt_dir / "meta.json").read_text())
    model = TrajectoryTransformer(
        input_dim=len(FEATURE_COLS), output_dim=1, task="binary",
        aux_dim=meta.get("aux_dim", N_FAILURE_CLASSES),
    ).to(device)
    model.load_state_dict(
        torch.load(ckpt_dir / "model.pt", map_location=device, weights_only=True))

    p_succ, _ = predict(model, Xn, torch.from_numpy(lengths), te,
                        OPERATING_FRAC, device)
    p_fail = 1.0 - p_succ

    print(f"  {planet:9} {mode:13} n={len(te):5}  P(fail) "
          f"min={p_fail.min():.6f} max={p_fail.max():.6f} std={p_fail.std():.2e}")

    out = {
        f"{planet}__{mode}__p_fail": p_fail.astype(np.float32),
        f"{planet}__{mode}__y": y[te].astype(np.int8),
    }
    if failure_type is not None:
        out[f"{planet}__{mode}__mode"] = failure_type[te].astype(np.int8)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--planets", nargs="+",
                    default=["venus", "mars", "mercury", "jupiter"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--data-dir", default="data/per_planet")
    ap.add_argument("--work-root", default="models/_norm_ablation")
    ap.add_argument("--out", default="reports/prediction_traces.npz")
    args = ap.parse_args()

    device = torch.device("cpu")   # inference only; keeps the GPU free
    work_root, data_dir = Path(args.work_root), Path(args.data_dir)

    print(f"\n  Replaying held-out predictions from {work_root}\n")
    payload: dict[str, np.ndarray] = {}
    for planet in args.planets:
        for mode in CONDITIONS:
            got = trace_one(planet, mode, work_root, data_dir, args.seed, device)
            if got:
                payload.update(got)

    if not payload:
        print("\n  Nothing collected — run python -m src.ml.norm_ablation first.\n")
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, **payload)
    print(f"\n  Saved {len(payload)} arrays -> {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
