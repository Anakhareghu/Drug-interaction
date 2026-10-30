"""
audit_final_concentration_readiness.py
======================================
Final Plasma Concentration Dataset Audit

Audits the strict concentration-only dataset (data/processed/pk_phase3_concentration_only.csv)
and creates data/processed/pk_final_concentration_readiness_summary.csv.

Outputs:
  - data/processed/pk_final_concentration_readiness_summary.csv
  - outputs/figures/final_plasma_concentration_profiles.png
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

WORKSPACE_DIR = Path(__file__).parent.parent
CONC_DATA = WORKSPACE_DIR / "data" / "processed" / "pk_phase3_concentration_only.csv"
OUT_CSV = WORKSPACE_DIR / "data" / "processed" / "pk_final_concentration_readiness_summary.csv"
FIGURES_DIR = WORKSPACE_DIR / "outputs" / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def main():
    if not CONC_DATA.exists():
        print(f"Concentration-only dataset not found: {CONC_DATA}")
        return
        
    df_conc = pd.read_csv(CONC_DATA)
    print(f"Loaded {len(df_conc)} concentration observation rows across {df_conc['drug_name'].nunique()} drugs.")
    
    audit_rows = []
    
    grouped = df_conc.groupby(["pkdb_id", "drug_name", "chembl_id"], sort=False)
    
    for (pkdb_id, drug_name, chembl_id), group in grouped:
        t_list = sorted(list(group["time_hr"].dropna().unique()))
        n_t_pts = len(t_list)
        min_t = round(float(min(t_list)), 2) if n_t_pts > 0 else np.nan
        max_t = round(float(max(t_list)), 2) if n_t_pts > 0 else np.nan
        
        min_c = round(float(group["value_std"].min()), 12)
        max_c = round(float(group["value_std"].max()), 12)
        
        units = sorted(list(group["unit_std"].dropna().astype(str).unique()))
        unit_str = "; ".join(units)
        
        n_obs = len(group)
        n_studies = group["study_sid"].nunique()
        is_sparse = bool(group["sparse_sampling"].iloc[0]) if "sparse_sampling" in group.columns else False
        
        if n_t_pts >= 2:
            status = "READY_FOR_PHASE3"
            explanation = "Valid plasma concentration trajectory with multiple post-dose time points."
        else:
            status = "DEFERRED"
            explanation = "Insufficient time-series resolution."
            
        audit_rows.append({
            "drug_name": drug_name,
            "pkdb_id": pkdb_id,
            "chembl_id": chembl_id,
            "total_plasma_obs": n_obs,
            "unique_time_points_count": n_t_pts,
            "time_points_list_hr": str([round(float(t), 2) for t in t_list]),
            "min_time_hr": min_t,
            "max_time_hr": max_t,
            "concentration_unit": unit_str,
            "min_conc_value": min_c,
            "max_conc_value": max_c,
            "number_of_studies": n_studies,
            "sparse_sampling_flag": is_sparse,
            "final_readiness_status": status,
            "explanation": explanation,
        })
        
    df_audit = pd.DataFrame(audit_rows)
    df_audit.to_csv(OUT_CSV, index=False)
    print(f"Saved final concentration readiness summary to {OUT_CSV}")
    
    # Generate visualization plot for concentration profiles
    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    
    drugs = df_conc["pkdb_id"].unique()
    colors = plt.cm.Set1(np.linspace(0, 1, max(len(drugs), 1)))
    
    for idx, d_sid in enumerate(drugs):
        sub_df = df_conc[df_conc["pkdb_id"] == d_sid].sort_values(by="time_hr")
        label_str = f"{d_sid} ({len(sub_df)} obs)"
        ax.plot(sub_df["time_hr"], sub_df["value_std"], marker="s", markersize=6, linestyle="-", linewidth=2.0, color=colors[idx], label=label_str, alpha=0.85)
        
    ax.set_title("Plasma Concentration C(t) Profiles for Phase 3 Ready Cohort", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Time (hours)", fontsize=11, labelpad=8)
    ax.set_ylabel("Plasma Concentration (mole / liter)", fontsize=11, labelpad=8)
    ax.set_yscale("log")
    ax.legend(frameon=True, facecolor="white", edgecolor="#e0e0e0", fontsize=10)
    plt.tight_layout()
    
    fig_path = FIGURES_DIR / "final_plasma_concentration_profiles.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved final plasma concentration plot to {fig_path}")

if __name__ == "__main__":
    main()
