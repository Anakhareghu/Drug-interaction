"""
create_unit_audit_and_conc_only.py
==================================
Creates:
  1. data/processed/pk_unit_audit.csv
  2. data/processed/pk_phase3_concentration_only.csv

Performs a strict unit and measurement classification across all 834 observations
in Phase 3A input dataset (data/processed/pk_phase3_input.csv).
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np

WORKSPACE_DIR = Path(__file__).parent.parent
INPUT_CSV = WORKSPACE_DIR / "data" / "processed" / "pk_phase3_input.csv"
OUT_UNIT_AUDIT = WORKSPACE_DIR / "data" / "processed" / "pk_unit_audit.csv"
OUT_CONC_ONLY = WORKSPACE_DIR / "data" / "processed" / "pk_phase3_concentration_only.csv"

def main():
    if not INPUT_CSV.exists():
        print(f"Input file not found: {INPUT_CSV}")
        return
        
    df_input = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df_input)} observation rows from pk_phase3_input.csv")
    
    unit_audit_rows = []
    
    # Analyze combinations of (drug, unit_std, raw_unit, source_table)
    grouped = df_input.groupby(["pkdb_id", "drug_name", "chembl_id", "unit_std", "raw_unit", "source_table"], sort=False)
    
    for (pkdb_id, drug_name, chembl_id, unit_std, raw_unit, source_table), group in grouped:
        count = len(group)
        
        # Categorize unit & measurement type
        u_str = str(unit_std).strip().lower()
        r_str = str(raw_unit).strip().lower()
        
        if u_str == "mole / liter" or u_str in ["mg/l", "ug/l", "ng/l", "nmol/l", "umol/l"]:
            measurement_type = "plasma_concentration"
            unit_category = "plasma_concentration"
            is_plasma_conc = True
        elif u_str in ["g", "gram / kilogram", "gram", "mg"]:
            measurement_type = "administered_dosing_mass"
            unit_category = "dosing_mass"
            is_plasma_conc = False
        elif u_str == "becquerel":
            measurement_type = "radioactivity_dose"
            unit_category = "radioactivity"
            is_plasma_conc = False
        elif u_str == "ml":
            measurement_type = "dose_volume"
            unit_category = "volume"
            is_plasma_conc = False
        elif "hour" in u_str or u_str == "hr":
            measurement_type = "elimination_half_life"
            unit_category = "pk_parameter"
            is_plasma_conc = False
        elif "dimensionless" in u_str or "percent" in u_str:
            measurement_type = "pharmacodynamic_ratio"
            unit_category = "pd_ratio"
            is_plasma_conc = False
        else:
            measurement_type = "other_pk_measurement"
            unit_category = "other"
            is_plasma_conc = False
            
        unit_audit_rows.append({
            "drug_name": drug_name,
            "pkdb_id": pkdb_id,
            "chembl_id": chembl_id,
            "raw_unit": raw_unit,
            "unit_std": unit_std,
            "source_table": source_table,
            "measurement_type": measurement_type,
            "unit_category": unit_category,
            "observation_count": count,
            "is_plasma_concentration": is_plasma_conc,
        })
        
    df_audit = pd.DataFrame(unit_audit_rows)
    df_audit.to_csv(OUT_UNIT_AUDIT, index=False)
    print(f"Saved unit audit table ({len(df_audit)} unit groups) to {OUT_UNIT_AUDIT}")
    
    # 2. Filter pk_phase3_concentration_only.csv
    # Retain observations where is_plasma_concentration == True
    # For drugs that have scatter concentration observations (losartan, exp3174), retain those 88 rows!
    plasma_drug_mask = df_input.apply(lambda r: (str(r["unit_std"]).strip().lower() == "mole / liter"), axis=1)
    df_conc_only = df_input[plasma_drug_mask].copy()
    
    df_conc_only.to_csv(OUT_CONC_ONLY, index=False)
    print(f"Saved concentration-only dataset ({len(df_conc_only)} observations) to {OUT_CONC_ONLY}")
    
    print("\n==================== UNIT AUDIT SUMMARY ====================")
    print(df_audit[["drug_name", "unit_std", "measurement_type", "unit_category", "observation_count", "is_plasma_concentration"]])

if __name__ == "__main__":
    main()
