# rf3_single_target_metrics.py
# RF3 metrics extraction for single-target-chain (monomer target) binder designs
import os
import glob
import numpy as np
import pandas as pd


def best_chain_plddt(chain_rows: pd.DataFrame, chain_id: str):
    """Find the batch with highest pLDDT for a given chain."""
    r = chain_rows[chain_rows["chain_chainwise"] == chain_id].copy()
    if r.empty:
        return (np.nan, np.nan)
    r["chainwise_plddt"] = pd.to_numeric(r["chainwise_plddt"], errors="coerce")
    idx = r["chainwise_plddt"].idxmax()
    return (float(r.loc[idx, "chainwise_plddt"]), int(r.loc[idx, "batch_idx"]))


def best_interface_min_pae(iface_rows: pd.DataFrame, a: str, b: str):
    """Find the batch with lowest min_pae at interface between chains a and b."""
    r = iface_rows[
        ((iface_rows["chain_i_interface"] == a) & (iface_rows["chain_j_interface"] == b)) |
        ((iface_rows["chain_i_interface"] == b) & (iface_rows["chain_j_interface"] == a))
    ].copy()
    if r.empty:
        return dict(
            best_min_pae=np.nan,
            best_min_pae_batch=np.nan,
            ipsae_at_best=np.nan,
            pae_at_best=np.nan,
            pde_at_best=np.nan,
        )

    for col in ["min_pae_interface", "ipsae_interface", "pae_interface", "pde_interface"]:
        if col in r.columns:
            r[col] = pd.to_numeric(r[col], errors="coerce")

    idx = r["min_pae_interface"].idxmin()
    return {
        "best_min_pae": float(r.loc[idx, "min_pae_interface"]),
        "best_min_pae_batch": int(r.loc[idx, "batch_idx"]),
        "ipsae_at_best": float(r.loc[idx, "ipsae_interface"]) if "ipsae_interface" in r.columns else np.nan,
        "pae_at_best": float(r.loc[idx, "pae_interface"]) if "pae_interface" in r.columns else np.nan,
        "pde_at_best": float(r.loc[idx, "pde_interface"]) if "pde_interface" in r.columns else np.nan,
    }


def summarize_score(score_path: str, binder: str, target: str):
    """Summarize a single .score file for a binder + single target chain."""
    df = pd.read_csv(score_path)

    chain_rows = df[df["chain_chainwise"].notna()].copy()
    iface_rows = df[df["chain_i_interface"].notna()].copy()

    design_id = os.path.basename(score_path).replace(".score", "")

    # Binder pLDDT
    best_binder_plddt, best_binder_batch = best_chain_plddt(chain_rows, binder)

    # Target pLDDT
    best_target_plddt, best_target_batch = best_chain_plddt(chain_rows, target)

    # Binder-Target interface
    iface = best_interface_min_pae(iface_rows, binder, target)

    # Overall metrics from first row
    overall_plddt = np.nan
    overall_pae = np.nan
    overall_ipsae = np.nan
    if not chain_rows.empty:
        tmp = chain_rows.iloc[0]
        overall_plddt = float(pd.to_numeric(tmp.get("overall_plddt"), errors="coerce"))
        overall_pae = float(pd.to_numeric(tmp.get("overall_pae"), errors="coerce"))
        overall_ipsae = float(pd.to_numeric(tmp.get("overall_ipsae"), errors="coerce"))

    return {
        "design_id": design_id,
        "score_path": score_path,

        "best_binder_plddt": best_binder_plddt,
        "best_binder_plddt_batch": best_binder_batch,

        "best_target_plddt": best_target_plddt,
        "best_target_plddt_batch": best_target_batch,

        "best_min_pae": iface["best_min_pae"],
        "best_min_pae_batch": iface["best_min_pae_batch"],
        "ipsae_at_best": iface["ipsae_at_best"],
        "pae_at_best": iface["pae_at_best"],
        "pde_at_best": iface["pde_at_best"],

        "overall_plddt": overall_plddt,
        "overall_pae": overall_pae,
        "overall_ipsae": overall_ipsae,
    }


def gather_rf3_metrics_single_target(
    parent: str,
    binder: str = "A_1",
    target: str = "B_1",
    out_csv: str | None = None,
    recursive: bool = True,
):
    """
    Gather RF3 metrics from all .score files under `parent`.

    Parameters
    ----------
    parent : str
        Directory containing RF3 output folders
    binder : str
        Chain ID for the binder (default "A_1")
    target : str
        Chain ID for the single target chain (default "B_1")
    out_csv : str, optional
        Path to save the gathered metrics CSV
    recursive : bool
        Search subdirectories recursively (default True)

    Returns
    -------
    pd.DataFrame
        DataFrame with one row per design
    """
    parent = os.path.abspath(parent)
    pattern = os.path.join(parent, "**", "*.score") if recursive else os.path.join(parent, "*.score")
    score_files = sorted(glob.glob(pattern, recursive=recursive))

    if not score_files:
        raise FileNotFoundError(f"No .score files found under: {parent}")

    records = []
    bad = 0
    for p in score_files:
        try:
            records.append(summarize_score(p, binder=binder, target=target))
        except Exception as e:
            bad += 1
            print(f"[WARN] Failed on {p}: {e}")

    out = pd.DataFrame(records)

    if out_csv is not None:
        out_csv = os.path.abspath(out_csv)
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)
        out.to_csv(out_csv, index=False)
        print(f"Wrote: {out_csv}")

    print(f"Found: {len(score_files)}   OK: {len(out)}   Failed: {bad}")
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gather RF3 metrics for single-target binder designs")
    parser.add_argument("parent", help="Directory containing RF3 output folders")
    parser.add_argument("--binder", default="A_1", help="Binder chain ID (default: A_1)")
    parser.add_argument("--target", default="B_1", help="Target chain ID (default: B_1)")
    parser.add_argument("--out-csv", help="Output CSV path")
    parser.add_argument("--no-recursive", action="store_true", help="Don't search recursively")

    args = parser.parse_args()

    gather_rf3_metrics_single_target(
        parent=args.parent,
        binder=args.binder,
        target=args.target,
        out_csv=args.out_csv,
        recursive=not args.no_recursive,
    )
