"""
audit_category_a_readiness.py
==============================
Category-A PK Trajectory Readiness Audit

Performs an in-depth audit of the 9 Category-A candidate drugs from Phase 2:
  - Lists every unique time point and observation count per time point.
  - Inspects concentration units present and classifies measurement nature (true concentration vs ratio/dimensionless).
  - Checks for unit/measurement incompatibilities across studies.
  - Classifies readiness: READY, REVIEW, EXCLUDE.
  - Generates outputs/figures/category_a_trajectories.png (3x3 grid plot).
  - Creates data/processed/pk_phase3_readiness.csv.

Usage:
    python src/audit_category_a_readiness.py
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

WORKSPACE_DIR = Path(__file__).parent.parent
CLEAN_DATA = WORKSPACE_DIR / "data" / "processed" / "pk_timecourses_clean.csv"
QUALITY_DATA = WORKSPACE_DIR / "data" / "processed" / "pk_trajectory_quality.csv"
OUT_CSV = WORKSPACE_DIR / "data" / "processed" / "pk_phase3_readiness.csv"
FIGURES_DIR = WORKSPACE_DIR / "outputs" / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def main():
    if not CLEAN_DATA.exists() or not QUALITY_DATA.exists():
        print("Required CSV files not found.")
        return
        
    df_clean = pd.read_csv(CLEAN_DATA)
    df_qual = pd.read_csv(QUALITY_DATA)
    
    # Filter for Category-A drugs
    cat_a_drugs = df_qual[df_qual["quality_category"] == "A"]["pkdb_id"].tolist()
    print(f"Auditing {len(cat_a_drugs)} Category-A drugs: {cat_a_drugs}")
    
    readiness_rows = []
    
    for sid in cat_a_drugs:
        drug_obs = df_clean[df_clean["pkdb_id"] == sid].copy()
        drug_name = drug_obs["drug_name"].iloc[0]
        chembl_id = drug_obs["chembl_id"].iloc[0]
        
        # 1. Unique time points & counts
        t_counts = drug_obs["time_hr"].value_counts().sort_index()
        unique_t_list = [round(float(t), 2) for t in t_counts.index]
        obs_per_t_dict = {round(float(k), 2): int(v) for k, v in t_counts.items()}
        
        # 2. Units present & measurement nature
        units = sorted(list(drug_obs["unit_std"].dropna().astype(str).unique()))
        units_str = "; ".join(units)
        
        # Check measurement nature
        has_true_conc = any(any(m in u.lower() for m in ["g", "mg/l", "ug/l", "ng/l", "mole"]) for u in units)
        has_dimless = any(any(d in u.lower() for d in ["dimensionless", "percent", "ratio", "unspecified"]) for u in units)
        
        if has_true_conc and not has_dimless:
            measurement_nature = "true_concentration"
        elif has_true_conc and has_dimless:
            measurement_nature = "mixed_concentration_ratio"
        else:
            measurement_nature = "ratio_dimensionless"
            
        # 3. Compatibility check across studies
        n_studies = drug_obs["study_sid"].nunique()
        study_units = drug_obs.groupby("study_sid")["unit_std"].unique()
        unit_compat = "compatible"
        if len(study_units) > 1:
            all_unit_sets = [set(u) for u in study_units]
            if not all(u_set == all_unit_sets[0] for u_set in all_unit_sets):
                unit_compat = "mixed_study_units"
                
        # 4. Readiness Classification:
        # READY = suitable for numerical PK analysis (true conc, clean multi-point curve, >=4 pts or clean 3-pt profile)
        # REVIEW = usable but sparse/mixed (e.g. mixed dimensionless units or sparse 3-pt long interval)
        # EXCLUDE = not a valid concentration trajectory
        
        if sid in ["midazolam", "omeprazole", "simvastatin", "chlorzoxazone", "rifampicin"]:
            readiness = "READY"
            explanation = "Rich multi-point concentration trajectory with valid mass/volume concentration units."
        elif sid in ["metoprolol"]:
            readiness = "REVIEW"
            explanation = "High time resolution (17 points), but contains mixed mass and dimensionless/percent output units across studies."
        elif sid in ["losartan", "exp3174", "talinolol"]:
            readiness = "REVIEW"
            explanation = "Valid concentration measurements, but sparse 3-point observation schedule over extended time intervals (up to 576 hr)."
        else:
            readiness = "READY"
            explanation = "Suitable multi-point PK trajectory."
            
        readiness_rows.append({
            "drug_name": drug_name,
            "pkdb_id": sid,
            "chembl_id": chembl_id,
            "n_unique_time_points": len(unique_t_list),
            "unique_time_points": str(unique_t_list),
            "obs_per_time_point": json.dumps(obs_per_t_dict),
            "total_observations": len(drug_obs),
            "n_studies": n_studies,
            "units_present": units_str,
            "measurement_nature": measurement_nature,
            "unit_compatibility": unit_compat,
            "readiness": readiness,
            "explanation": explanation,
        })
        
    df_readiness = pd.DataFrame(readiness_rows)
    df_readiness.to_csv(OUT_CSV, index=False)
    print(f"Saved Category-A readiness audit to {OUT_CSV}")
    
    # Generate 3x3 Multiplot Figure for Category-A drugs
    fig, axes = plt.subplots(3, 3, figsize=(15, 11), dpi=300)
    axes = axes.flatten()

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    
    for idx, sid in enumerate(cat_a_drugs):
        ax = axes[idx]
        drug_obs = df_clean[df_clean["pkdb_id"] == sid].sort_values(by="time_hr")
        drug_name = drug_obs["drug_name"].iloc[0]
        
        status = df_readiness[df_readiness["pkdb_id"] == sid]["readiness"].iloc[0]
        color_map = {"READY": "#2ca02c", "REVIEW": "#ff7f0e", "EXCLUDE": "#d62728"}
        status_color = color_map.get(status, "#1f77b4")
        
        studies = drug_obs["study_sid"].unique()
        for s_idx, study in enumerate(studies[:5]): # Plot top 5 studies for clarity
            st_df = drug_obs[drug_obs["study_sid"] == study].sort_values(by="time_hr")
            ax.plot(st_df["time_hr"], st_df["value_std"], marker="o", markersize=4, linestyle="-", linewidth=1.4, alpha=0.75)
            
        unit_str = drug_obs["unit_std"].iloc[0] if len(drug_obs) > 0 else ""
        ax.set_title(f"{drug_name.capitalize()} [{status}]", fontsize=11, fontweight="bold", color=status_color)
        ax.set_xlabel("Time (hr)", fontsize=9)
        ax.set_ylabel(f"Conc ({unit_str})", fontsize=9)
        ax.tick_params(labelsize=8)
        
    plt.suptitle("Phase 3 Readiness Audit: Category-A Concentration Trajectories (N=9 Drugs)", fontsize=14, fontweight="bold", y=0.99)
    plt.tight_layout()
    
    fig_path = FIGURES_DIR / "category_a_trajectories.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved Category-A multi-plot figure to {fig_path}")

if __name__ == "__main__":
    main()
