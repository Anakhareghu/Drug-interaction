"""
audit_pk_trajectories.py
========================
PK Trajectory Quality Audit

Audits the cleaned Phase 2 dataset (data/processed/pk_timecourses_clean.csv)
to evaluate the time-series granularity of each drug before Phase 3.

Calculates per drug:
  - number of unique time points
  - min and max time (hours)
  - number of studies
  - number of valid concentration observations
  - concentration units present
  - whether time varies beyond 0
  - whether dimensionless/non-concentration units are present
  - quality classification (A, B, C):
      A = meaningful time-series (>=3 distinct time points)
      B = limited time-series (2 distinct time points)
      C = no usable time-series (1 distinct time point)

Outputs:
  - data/processed/pk_trajectory_quality.csv
  - outputs/figures/quality_category_distribution.png
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

WORKSPACE_DIR = Path(__file__).parent.parent
CLEAN_DATA = WORKSPACE_DIR / "data" / "processed" / "pk_timecourses_clean.csv"
OUT_CSV = WORKSPACE_DIR / "data" / "processed" / "pk_trajectory_quality.csv"
FIGURES_DIR = WORKSPACE_DIR / "outputs" / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def main():
    if not CLEAN_DATA.exists():
        print(f"File not found: {CLEAN_DATA}")
        return
        
    df_clean = pd.read_csv(CLEAN_DATA)
    print(f"Loaded {len(df_clean)} observations across {df_clean['drug_name'].nunique()} drugs.")
    
    audit_rows = []
    
    # Group by drug
    grouped = df_clean.groupby(["pkdb_id", "drug_name", "chembl_id"], sort=False)
    
    for (pkdb_id, drug_name, chembl_id), group in grouped:
        # Unique time points
        unique_t = sorted(group["time_hr"].dropna().unique())
        n_unique_t = len(unique_t)
        min_t = min(unique_t) if n_unique_t > 0 else np.nan
        max_t = max(unique_t) if n_unique_t > 0 else np.nan
        
        n_studies = group["study_sid"].nunique()
        n_obs = len(group)
        
        # Units present
        units = [str(u) for u in group["unit_std"].dropna().unique()]
        units_str = "; ".join(sorted(units))
        
        time_varies = bool(max_t > 0)
        
        # Check for dimensionless / non-concentration / fraction units
        dimless_keywords = ["dimensionless", "fraction", "ratio", "percent", "%", "normalized", "unspecified"]
        has_dimless = any(any(kw in u.lower() for kw in dimless_keywords) for u in units)
        
        # Category classification:
        # A = >= 3 distinct time points
        # B = 2 distinct time points
        # C = 1 distinct time point
        if n_unique_t >= 3:
            category = "A"
        elif n_unique_t == 2:
            category = "B"
        else:
            category = "C"
            
        audit_rows.append({
            "drug_name": drug_name,
            "pkdb_id": pkdb_id,
            "chembl_id": chembl_id,
            "unique_time_points": n_unique_t,
            "min_time_hr": round(float(min_t), 2) if pd.notna(min_t) else np.nan,
            "max_time_hr": round(float(max_t), 2) if pd.notna(max_t) else np.nan,
            "n_studies": n_studies,
            "n_observations": n_obs,
            "units_present": units_str,
            "time_varies_beyond_0": time_varies,
            "has_dimensionless_units": has_dimless,
            "quality_category": category,
        })
        
    df_audit = pd.DataFrame(audit_rows)
    # Sort by quality_category (A, B, C), unique_time_points desc, n_observations desc
    df_audit = df_audit.sort_values(by=["quality_category", "unique_time_points", "n_observations"], ascending=[True, False, False])
    
    df_audit.to_csv(OUT_CSV, index=False)
    print(f"Saved quality audit results ({len(df_audit)} drugs) to {OUT_CSV}")
    
    # Counts by category
    cat_counts = df_audit["quality_category"].value_counts().reindex(["A", "B", "C"]).fillna(0).astype(int)
    print("\n==================== AUDIT SUMMARY ====================")
    print(f"Category A (Meaningful time-series, >=3 time points): {cat_counts.get('A', 0)} drugs")
    print(f"Category B (Limited time-series, 2 time points)     : {cat_counts.get('B', 0)} drugs")
    print(f"Category C (No usable time-series, 1 time point)    : {cat_counts.get('C', 0)} drugs")
    
    # Plot distribution
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    bars = ax.bar(["Category A\n(>=3 Time Points)", "Category B\n(2 Time Points)", "Category C\n(1 Time Point)"], 
                  [cat_counts["A"], cat_counts["B"], cat_counts["C"]],
                  color=["#2ca02c", "#ff7f0e", "#d62728"], width=0.55, edgecolor="black", linewidth=0.8)
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),  # 4 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
                    
    ax.set_title("Distribution of PK Trajectory Quality Categories (N=36 Drugs)", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Number of Candidate Drugs", fontsize=11, labelpad=8)
    ax.set_ylim(0, max(cat_counts) + 5)
    plt.tight_layout()
    
    fig_path = FIGURES_DIR / "quality_category_distribution.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved category distribution plot to {fig_path}")

if __name__ == "__main__":
    main()
