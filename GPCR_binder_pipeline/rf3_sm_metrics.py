# rf3_sm_metrics.py
import os
import glob
import numpy as np
import pandas as pd

def _col(prefix: str, i: int) -> str:
    return f"{prefix}_{i}"

def _cols(prefix: str, n_models: int = 5):
    return [_col(prefix, i) for i in range(n_models)]

def _to_num(x):
    return pd.to_numeric(x, errors="coerce")

def _best_idx_from_row(row: pd.Series, prefixes: list[str], n_models: int, mode: str):
    """
    Choose best model index for a single design row.

    mode:
      - "max_iptm_pl" (default): maximize iptm.iptm_protein_ligand
      - "max_iptm"            : maximize iptm.iptm
      - "max_ptm"             : maximize ptm.ptm
      - "min_clash_then_max_iptm_pl": prefer no-clash models first, then maximize iptm_pl
    """
    # fetch arrays
    ptm = np.array([_to_num(row.get(_col("ptm.ptm", i))) for i in range(n_models)], dtype=float)
    iptm = np.array([_to_num(row.get(_col("iptm.iptm", i))) for i in range(n_models)], dtype=float)
    iptm_pl = np.array([_to_num(row.get(_col("iptm.iptm_protein_ligand", i))) for i in range(n_models)], dtype=float)
    clash = np.array([_to_num(row.get(_col("count_clashing_chains.has_clash", i))) for i in range(n_models)], dtype=float)

    # valid mask: require metric to be finite
    if mode == "max_iptm_pl":
        score = iptm_pl
        valid = np.isfinite(score)
        if not valid.any():
            return np.nan
        return int(np.nanargmax(score))

    if mode == "max_iptm":
        score = iptm
        valid = np.isfinite(score)
        if not valid.any():
            return np.nan
        return int(np.nanargmax(score))

    if mode == "max_ptm":
        score = ptm
        valid = np.isfinite(score)
        if not valid.any():
            return np.nan
        return int(np.nanargmax(score))

    if mode == "min_clash_then_max_iptm_pl":
        # prefer clash==0; if none, fall back to all
        no_clash = (clash == 0) & np.isfinite(iptm_pl)
        if no_clash.any():
            idxs = np.where(no_clash)[0]
            # among those, pick highest iptm_pl
            best = idxs[np.nanargmax(iptm_pl[idxs])]
            return int(best)
        # fallback
        valid = np.isfinite(iptm_pl)
        if not valid.any():
            return np.nan
        return int(np.nanargmax(iptm_pl))

    raise ValueError(f"Unknown mode: {mode}")

def _add_best_columns(df: pd.DataFrame, n_models: int = 5, mode: str = "max_iptm_pl"):
    """
    For each row (example_id), compute best_model_idx and best_* metrics pulled from that model.
    """
    df = df.copy()

    # ensure numeric for all model columns we might use
    for prefix in [
        "ptm.ptm",
        "iptm.iptm",
        "iptm.iptm_protein_ligand",
        "iptm.iptm_protein_protein",
        "iptm.iptm_ligand_ligand",
        "count_clashing_chains.has_clash",
    ]:
        for c in _cols(prefix, n_models):
            if c in df.columns:
                df[c] = _to_num(df[c])

    best_idx = []
    for _, row in df.iterrows():
        best_idx.append(_best_idx_from_row(row, [], n_models=n_models, mode=mode))
    df["best_model_idx"] = best_idx

    # helper to pull value at best idx
    def pull(prefix):
        out = np.full(len(df), np.nan, dtype=float)
        for i in range(n_models):
            col = _col(prefix, i)
            if col not in df.columns:
                continue
            mask = df["best_model_idx"] == i
            out[mask.values] = df.loc[mask, col].to_numpy(float)
        return out

    df["best_ptm"] = pull("ptm.ptm")
    df["best_iptm"] = pull("iptm.iptm")
    df["best_iptm_protein_ligand"] = pull("iptm.iptm_protein_ligand")
    df["best_iptm_protein_protein"] = pull("iptm.iptm_protein_protein")
    df["best_iptm_ligand_ligand"] = pull("iptm.iptm_ligand_ligand")
    df["best_has_clash"] = pull("count_clashing_chains.has_clash")

    # also useful summary flags
    clash_cols = [c for c in _cols("count_clashing_chains.has_clash", n_models) if c in df.columns]
    if clash_cols:
        df["any_clash"] = (df[clash_cols].max(axis=1) > 0)
        df["n_models_with_clash"] = (df[clash_cols] > 0).sum(axis=1)
    else:
        df["any_clash"] = False
        df["n_models_with_clash"] = 0

    return df

def _add_summary_stats(df: pd.DataFrame, n_models: int = 5):
    """
    Optional: add mean/std/min/max across the 5 models for key metrics.
    """
    df = df.copy()

    def stats(prefix, name):
        cols = [c for c in _cols(prefix, n_models) if c in df.columns]
        if not cols:
            return
        arr = df[cols].to_numpy(float)
        df[f"{name}_mean"] = np.nanmean(arr, axis=1)
        df[f"{name}_std"]  = np.nanstd(arr, axis=1)
        df[f"{name}_min"]  = np.nanmin(arr, axis=1)
        df[f"{name}_max"]  = np.nanmax(arr, axis=1)

    stats("iptm.iptm_protein_ligand", "iptmPL")
    stats("ptm.ptm", "ptm")
    stats("iptm.iptm", "iptm")
    return df

def gather_rf3_small_molecule_metrics(
    parent: str,
    pattern: str = "*.csv",
    recursive: bool = True,
    out_csv: str | None = None,
    n_models: int = 5,
    best_mode: str = "max_iptm_pl",
    add_stats: bool = False,
    keep_source_path: bool = True,
) -> pd.DataFrame:
    """
    Collect all RF3 small-molecule metrics CSVs under `parent`, merge, deduplicate by example_id,
    pick best model per design, and write one out CSV.

    best_mode:
      - "max_iptm_pl" (recommended default)
      - "min_clash_then_max_iptm_pl" (often nicer in practice)
      - "max_iptm"
      - "max_ptm"
    """
    parent = os.path.abspath(parent)
    glob_pat = os.path.join(parent, "**", pattern) if recursive else os.path.join(parent, pattern)
    files = sorted(glob.glob(glob_pat, recursive=recursive))
    if not files:
        raise FileNotFoundError(f"No CSV files found under: {parent}  pattern={pattern}")

    parts = []
    bad = 0
    for f in files:
        try:
            d = pd.read_csv(f)
            if "example_id" not in d.columns:
                raise ValueError("missing example_id")
            if keep_source_path:
                d["source_csv"] = f
            parts.append(d)
        except Exception as e:
            bad += 1
            print(f"[WARN] Failed on {f}: {e}")

    raw = pd.concat(parts, ignore_index=True)

    # If the same example_id appears in multiple CSVs, keep the *first* occurrence
    # (or you can change this logic later)
    raw["example_id"] = raw["example_id"].astype(str)
    raw = raw.drop_duplicates(subset=["example_id"], keep="first").reset_index(drop=True)

    out = _add_best_columns(raw, n_models=n_models, mode=best_mode)
    if add_stats:
        out = _add_summary_stats(out, n_models=n_models)

    # Nice ordering of key columns up front
    front = [
        "example_id",
        "best_model_idx",
        "best_iptm_protein_ligand",
        "best_ptm",
        "best_iptm",
        "best_has_clash",
        "any_clash",
        "n_models_with_clash",
    ]
    if keep_source_path:
        front.append("source_csv")

    cols = front + [c for c in out.columns if c not in front]
    out = out[cols]

    if out_csv:
        out_csv = os.path.abspath(out_csv)
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)
        out.to_csv(out_csv, index=False)
        print(f"Wrote: {out_csv}")

    print(f"Files: {len(files)}   Designs: {len(out)}   Failed files: {bad}")
    return out