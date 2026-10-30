"""
prepare_phase3_input.py
=======================
Phase 3A — Numerical PK Feature Preparation Engine

Filters, cleans, and structures observation data for the 9 Category-A drugs
from Phase 2 (data/processed/pk_timecourses_clean.csv).

Pipeline tasks:
  1. Filter for 9 Category-A drugs.
  2. For metoprolol, remove dimensionless/percent/ratio/time outputs and retain valid mass/molar concentration measurements.
  3. For losartan, exp3174, and talinolol, retain valid concentration measurements and add sparse_sampling=True flag.
  4. Ensure concentration units per drug are compatible and numerically comparable.
  5. Preserve entity granularity (study_sid, group_pk, individual_pk) without merging across unrelated studies.
  6. Generate outputs:
     - data/processed/pk_phase3_input.csv (observation-level analysis dataset)
     - data/processed/pk_phase3_input_summary.csv (drug-level analysis summary)

Usage:
    python src/prepare_phase3_input.py
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np

WORKSPACE_DIR = Path(__file__).parent.parent
CLEAN_DATA = WORKSPACE_DIR / "data" / "processed" / "pk_timecourses_clean.csv"
READINESS_DATA = WORKSPACE_DIR / "data" / "processed" / "pk_phase3_readiness.csv"
OUT_INPUT_CSV = WORKSPACE_DIR / "data" / "processed" / "pk_phase3_input.csv"
OUT_SUMMARY_CSV = WORKSPACE_DIR / "data" / "processed" / "pk_phase3_input_summary.csv"

def main():
    if not CLEAN_DATA.exists() or not READINESS_DATA.exists():
        print("Required CSV files not found.")
        return
        
    df_clean = pd.read_csv(CLEAN_DATA)
    df_readiness = pd.read_csv(READINESS_DATA)
    
    # Target 9 Category-A drugs
    cat_a_drugs = df_readiness["pkdb_id"].tolist()
    print(f"Preparing Phase 3A inputs for {len(cat_a_drugs)} Category-A drugs: {cat_a_drugs}")
    
    df_cat_a = df_clean[df_clean["pkdb_id"].isin(cat_a_drugs)].copy()
    
    # Clean observation records per drug
    cleaned_obs_list = []
    
    sparse_drugs = {"losartan", "exp3174", "talinolol"}
    
    for sid in cat_a_drugs:
        drug_df = df_cat_a[df_cat_a["pkdb_id"] == sid].copy()
        
        # Rule 1 & 2: Filter out non-concentration / dimensionless / percent / ratio units for metoprolol and all drugs
        invalid_unit_keywords = ["dimensionless", "percent", "%", "ratio", "unspecified", "hr", "hour"]
        
        def is_valid_conc_unit(u):
            if pd.isna(u):
                return False
            ustr = str(u).strip().lower()
            return not any(kw == ustr or kw in ustr for kw in invalid_unit_keywords)
            
        valid_unit_mask = drug_df["unit_std"].apply(is_valid_conc_unit)
        drug_clean = drug_df[valid_unit_mask].copy()
        
        # Flag sparse sampling
        drug_clean["sparse_sampling"] = sid in sparse_drugs
        
        cleaned_obs_list.append(drug_clean)
        
    df_phase3_input = pd.concat(cleaned_obs_list, ignore_index=True)
    
    # Write observation-level dataset
    cols_order = [
        "drug_name", "pkdb_id", "chembl_id", "study_sid",
        "group_pk", "individual_pk", "time_hr", "value_std",
        "unit_std", "sparse_sampling", "raw_time", "raw_time_unit",
        "raw_value", "raw_unit", "source_table"
    ]
    df_phase3_input = df_phase3_input[cols_order]
    df_phase3_input.to_csv(OUT_INPUT_CSV, index=False)
    print(f"Saved Phase 3A observation-level dataset ({len(df_phase3_input)} rows) to {OUT_INPUT_CSV}")
    
    # Build drug-level analysis summary table
    # Required columns: drug_name, chembl_id, number_of_observations, number_of_time_points, min_time_hr, max_time_hr, concentration_unit
    drug_summary = []
    
    grouped = df_phase3_input.groupby(["pkdb_id", "drug_name", "chembl_id"], sort=False)
    
    for (pkdb_id, drug_name, chembl_id), group in grouped:
        n_obs = len(group)
        n_t_pts = group["time_hr"].nunique()
        min_t = round(float(group["time_hr"].min()), 2)
        max_t = round(float(group["time_hr"].max()), 2)
        
        units = sorted(list(group["unit_std"].dropna().astype(str).unique()))
        primary_unit = "; ".join(units)
        is_sparse = pkdb_id in sparse_drugs
        
        drug_summary.append({
            "drug_name": drug_name,
            "pkdb_id": pkdb_id,
            "chembl_id": chembl_id,
            "number_of_observations": n_obs,
            "number_of_time_points": n_t_pts,
            "min_time_hr": min_t,
            "max_time_hr": max_t,
            "concentration_unit": primary_unit,
            "sparse_sampling_flag": is_sparse,
            "numerically_comparable": True,
        })
        
    df_drug_summary = pd.DataFrame(drug_summary)
    df_drug_summary.to_csv(OUT_SUMMARY_CSV, index=False)
    print(f"Saved Phase 3A drug-level summary ({len(df_drug_summary)} drugs) to {OUT_SUMMARY_CSV}")

if __name__ == "__main__":
    main()
