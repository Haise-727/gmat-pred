"""
Second dataset: does pooled scaling also hurt outside the GMAT simulator?

Data: NASA C-MAPSS turbofan engine degradation (public, Saxena and Goebel 2008).
Each engine is a run to failure. FD001 has one operating condition, FD002 and
FD004 have six. The six conditions play the role the seven planets play in the
main experiment: the sensors sit at very different levels in each condition, and
the slow drift that shows the engine is wearing out is small next to that gap.

Task: look at the last 30 cycles of an engine and say whether it will fail within
30 cycles (RUL <= 30). The split is by engine, 70/15/15, so no engine appears in
two splits.

Two ways of scaling the 14 sensors that change over an engine's life:

  pooled     one median and IQR for every row, whatever the condition
  per-group  one median and IQR per operating condition

Same Transformer, same windows, same seed and epoch budget for both. XGBoost
reads the same scaled, flattened window, as in the main experiment. FD001 has a
single condition, so the two scalers are the same thing there. It is the control.

Everything is written to reports/second_dataset.json.

    python -m src.ml.second_dataset --data /path/to/CMAPSSData
"""

from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.cluster import KMeans
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

from src.ml.model import TrajectoryTransformer

REPORTS = Path(__file__).resolve().parents[2] / "reports"

COLS = ["unit", "cycle", "op1", "op2", "op3"] + [f"s{i}" for i in range(1, 22)]
# Sensors that actually change over an engine's life (the rest are constant).
SENSORS = [f"s{i}" for i in (2, 3, 4, 7, 8, 9, 11, 12, 13, 14, 15, 17, 20, 21)]
WINDOW = 30
HORIZON = 30
MODES = ["pooled", "per-group"]


# ── data ─────────────────────────────────────────────────────────────────────

def load_subset(data_dir: Path, name: str):
    df = pd.read_csv(data_dir / f"train_{name}.txt", sep=r"\s+", header=None, names=COLS)
    df["rul"] = df.groupby("unit")["cycle"].transform("max") - df["cycle"]
    n_cond = 1 if name in ("FD001", "FD003") else 6
    if n_cond == 1:
        df["group"] = 0
    else:
        z = df[["op1", "op2", "op3"]].to_numpy(float)
        z = (z - z.mean(0)) / (z.std(0) + 1e-9)
        df["group"] = KMeans(n_cond, n_init=10, random_state=0).fit_predict(z)
    return df, n_cond


def make_windows(df: pd.DataFrame):
    """One window per engine per cycle (from cycle WINDOW on)."""
    X, y, g, unit = [], [], [], []
    for u, e in df.groupby("unit"):
        v = e[SENSORS].to_numpy(np.float32)
        gg, rul = e["group"].to_numpy(), e["rul"].to_numpy()
        for t in range(WINDOW, len(e) + 1):
            X.append(v[t - WINDOW:t])
            y.append(int(rul[t - 1] <= HORIZON))
            g.append(gg[t - 1])
            unit.append(u)
    return np.stack(X), np.array(y), np.array(g), np.array(unit)


def split_units(units: np.ndarray, seed: int):
    u = np.unique(units)
    rng = np.random.default_rng(seed)
    rng.shuffle(u)
    n = len(u)
    n_tr, n_va = int(round(n * 0.70)), int(round(n * 0.15))
    return u[:n_tr], u[n_tr:n_tr + n_va], u[n_tr + n_va:]


# ── scaling ──────────────────────────────────────────────────────────────────

def fit_scaler(rows: np.ndarray, grp: np.ndarray, mode: str, n_groups: int):
    """Median and IQR per feature, fitted on training rows only."""
    def stats(a):
        med = np.median(a, 0)
        iqr = np.subtract(*np.percentile(a, [75, 25], 0))
        return med, np.where(iqr < 1e-6, 1.0, iqr)
    if mode == "pooled":
        m, s = stats(rows)
        return np.tile(m, (n_groups, 1)), np.tile(s, (n_groups, 1))
    ms = [stats(rows[grp == k]) for k in range(n_groups)]
    return np.stack([a for a, _ in ms]), np.stack([b for _, b in ms])


def row_groups(df: pd.DataFrame):
    """Group id of every row inside every window (needed because the condition
    changes cycle by cycle in FD002/FD004)."""
    out = []
    for _, e in df.groupby("unit"):
        gg = e["group"].to_numpy()
        for t in range(WINDOW, len(e) + 1):
            out.append(gg[t - WINDOW:t])
    return np.stack(out)


# ── model ────────────────────────────────────────────────────────────────────

def train_and_predict(Xtr, ytr, Xva, yva, Xte, seed, epochs, device):
    torch.manual_seed(seed)
    model = TrajectoryTransformer(input_dim=Xtr.shape[2], output_dim=1, task="binary").to(device)
    pos_w = torch.tensor([(ytr == 0).sum() / max((ytr == 1).sum(), 1)], device=device, dtype=torch.float32)
    crit = nn.BCEWithLogitsLoss(pos_weight=pos_w)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    Xtr_t = torch.from_numpy(Xtr).to(device)
    ytr_t = torch.from_numpy(ytr.astype(np.float32)).to(device)

    @torch.no_grad()
    def predict(X):
        model.eval()
        out = []
        for i in range(0, len(X), 1024):
            out.append(torch.sigmoid(model(torch.from_numpy(X[i:i + 1024]).to(device))).cpu())
        return torch.cat(out).numpy()

    best_auc, best_state = -1.0, None
    rng = np.random.default_rng(seed)
    for ep in range(epochs):
        model.train()
        order = rng.permutation(len(Xtr))
        for i in range(0, len(order), 256):
            b = order[i:i + 256]
            opt.zero_grad()
            crit(model(Xtr_t[b]), ytr_t[b]).backward()
            opt.step()
        sched.step()
        auc = roc_auc_score(yva, predict(Xva))
        if auc > best_auc:
            best_auc = auc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    return predict(Xva), predict(Xte), best_auc


# ── measurements ─────────────────────────────────────────────────────────────

def within_group_auc(y, p, g):
    vals = []
    for k in np.unique(g):
        m = g == k
        if len(np.unique(y[m])) == 2:
            vals.append(roc_auc_score(y[m], p[m]))
    return float(np.mean(vals)) if vals else float("nan")


def within_group_std(p, g):
    return float(np.mean([p[g == k].std() for k in np.unique(g)]))


def signal(Xs, rg):
    """Mean within-group std of the scaled features (the quantity pooling shrinks)."""
    rows = Xs.reshape(-1, Xs.shape[-1])
    gg = rg.reshape(-1)
    return float(np.mean([rows[gg == k].std(0).mean() for k in np.unique(gg)]))


def run_one(df, n_groups, mode, seed, epochs, device, cache):
    Xw, y, g, unit, rg = cache
    tr_u, va_u, te_u = split_units(unit, seed)
    tr, va, te = (np.isin(unit, s) for s in (tr_u, va_u, te_u))
    rows_tr = Xw[tr].reshape(-1, Xw.shape[-1])
    med, iqr = fit_scaler(rows_tr, rg[tr].reshape(-1), mode, n_groups)
    Xs = ((Xw - med[rg]) / iqr[rg]).astype(np.float32)   # each row uses its own group's statistics

    t0 = time.time()
    p_va, p_te, best_val = train_and_predict(Xs[tr], y[tr], Xs[va], y[va], Xs[te], seed, epochs, device)

    tree = XGBClassifier(n_estimators=300, max_depth=5, tree_method="hist", device=device.type,
                         eval_metric="logloss", random_state=seed, verbosity=0)
    tree.fit(Xs[tr].reshape(tr.sum(), -1), y[tr])
    p_tree = tree.predict_proba(Xs[te].reshape(te.sum(), -1))[:, 1]

    return dict(
        mode=mode, seed=seed,
        val_auc=float(best_val),
        test_auc=float(roc_auc_score(y[te], p_te)),
        tree_test_auc=float(roc_auc_score(y[te], p_tree)),
        pred_std_within_group=within_group_std(p_te, g[te]),
        tree_pred_std_within_group=within_group_std(p_tree, g[te]),
        pred_std_overall=float(p_te.std()),
        within_group_auc=within_group_auc(y[te], p_te, g[te]),
        tree_within_group_auc=within_group_auc(y[te], p_tree, g[te]),
        signal_ratio=signal(Xs[tr], rg[tr]),
        n_train=int(tr.sum()), n_test=int(te.sum()),
        seconds=round(time.time() - t0, 1),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True, help="folder with train_FD00x.txt")
    ap.add_argument("--subsets", nargs="+", default=["FD001", "FD002", "FD004"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--out", type=Path, default=REPORTS / "second_dataset.json")
    args = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    runs = []
    for name in args.subsets:
        df, n_groups = load_subset(args.data, name)
        Xw, y, g, unit = make_windows(df)
        cache = (Xw, y, g, unit, row_groups(df))
        print(f"\n{name}: {df.unit.nunique()} engines, {len(y)} windows, "
              f"{n_groups} condition(s), {y.mean():.1%} positive")
        for mode in MODES:
            for seed in args.seeds:
                r = run_one(df, n_groups, mode, seed, args.epochs, device, cache)
                r["subset"] = name
                runs.append(r)
                print(f"  {mode:9s} seed {seed}: val_auc {r['val_auc']:.4f}  tree {r['tree_test_auc']:.4f}  "
                      f"pred_std {r['pred_std_within_group']:.2e}  signal {r['signal_ratio']:.3f}  ({r['seconds']}s)")
                args.out.parent.mkdir(exist_ok=True)
                args.out.write_text(json.dumps(dict(
                    dataset="NASA C-MAPSS turbofan engine degradation",
                    window=WINDOW, horizon=HORIZON, epochs=args.epochs, sensors=SENSORS, runs=runs), indent=1))


if __name__ == "__main__":
    main()
