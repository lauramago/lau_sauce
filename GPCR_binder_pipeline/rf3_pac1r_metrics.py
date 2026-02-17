# rf3_metrics.py
import os, glob
import numpy as np
import pandas as pd

def best_chain_plddt(chain_rows: pd.DataFrame, chain_id: str):
    r = chain_rows[chain_rows["chain_chainwise"] == chain_id].copy()
    if r.empty:
        return (np.nan, np.nan)
    r["chainwise_plddt"] = pd.to_numeric(r["chainwise_plddt"], errors="coerce")
    idx = r["chainwise_plddt"].idxmax()
    return (float(r.loc[idx, "chainwise_plddt"]), int(r.loc[idx, "batch_idx"]))

def best_interface_min_pae(iface_rows: pd.DataFrame, a: str, b: str):
    r = iface_rows[
        ((iface_rows["chain_i_interface"] == a) & (iface_rows["chain_j_interface"] == b)) |
        ((iface_rows["chain_i_interface"] == b) & (iface_rows["chain_j_interface"] == a))
    ].copy()
    if r.empty:
        return dict(best_min_pae=np.nan, best_min_pae_batch=np.nan,
                    ipsae_at_best=np.nan, pae_at_best=np.nan, pde_at_best=np.nan)

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

def summarize_score(score_path: str, binder: str, targets: list[str]):
    df = pd.read_csv(score_path)

    chain_rows = df[df["chain_chainwise"].notna()].copy()
    iface_rows = df[df["chain_i_interface"].notna()].copy()

    design_id = os.path.basename(score_path).replace(".score", "")

    # binder chain best pLDDT
    best_binder_plddt, best_binder_batch = best_chain_plddt(chain_rows, binder)

    # overall metrics (same in each row; grab from first chain row if present)
    overall_plddt = np.nan
    overall_pae = np.nan
    overall_ipsae = np.nan
    if not chain_rows.empty:
        tmp = chain_rows.iloc[0]
        overall_plddt = float(pd.to_numeric(tmp.get("overall_plddt"), errors="coerce"))
        overall_pae   = float(pd.to_numeric(tmp.get("overall_pae"), errors="coerce"))
        overall_ipsae = float(pd.to_numeric(tmp.get("overall_ipsae"), errors="coerce"))

    out = {
        "design_id": design_id,
        "score_path": score_path,
        "best_binder_plddt": best_binder_plddt,
        "best_binder_plddt_batch": best_binder_batch,
        "overall_plddt": overall_plddt,
        "overall_pae": overall_pae,
        "overall_ipsae": overall_ipsae,
    }

    # per-target interface metrics
    per_target = []
    for t in targets:
        m = best_interface_min_pae(iface_rows, binder, t)
        out[f"{binder}-{t}_best_min_pae"] = m["best_min_pae"]
        out[f"{binder}-{t}_best_min_pae_batch"] = m["best_min_pae_batch"]
        out[f"{binder}-{t}_ipsae_at_best"] = m["ipsae_at_best"]
        out[f"{binder}-{t}_pae_at_best"] = m["pae_at_best"]
        out[f"{binder}-{t}_pde_at_best"] = m["pde_at_best"]
        per_target.append((t, m))

    # optional: best across ALL binder↔target interfaces (useful for multi-chain targets)
    # pick the target that gives the minimum min_pae_interface
    best_t = None
    best_val = np.inf
    best_m = None
    for t, m in per_target:
        v = m["best_min_pae"]
        if pd.notna(v) and v < best_val:
            best_val = v
            best_t = t
            best_m = m

    out["best_target_chain_by_min_pae"] = best_t if best_t is not None else np.nan
    out["best_any_target_min_pae"] = best_m["best_min_pae"] if best_m else np.nan
    out["best_any_target_min_pae_batch"] = best_m["best_min_pae_batch"] if best_m else np.nan
    out["best_any_target_ipsae_at_best"] = best_m["ipsae_at_best"] if best_m else np.nan
    out["best_any_target_pae_at_best"] = best_m["pae_at_best"] if best_m else np.nan
    out["best_any_target_pde_at_best"] = best_m["pde_at_best"] if best_m else np.nan

    return out

def gather_rf3_metrics(parent: str, binder: str, targets: list[str],
                       out_csv: str | None = None, recursive: bool = True):
    parent = os.path.abspath(parent)
    pattern = os.path.join(parent, "**", "*.score") if recursive else os.path.join(parent, "*.score")
    score_files = sorted(glob.glob(pattern, recursive=recursive))

    if not score_files:
        raise FileNotFoundError(f"No .score files found under: {parent}")

    records = []
    bad = 0
    for p in score_files:
        try:
            records.append(summarize_score(p, binder=binder, targets=targets))
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
