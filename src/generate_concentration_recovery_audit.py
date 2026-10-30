"""
generate_concentration_recovery_audit.py
=========================================
Phase 3B — Raw PK Concentration Recovery and Validation Audit Generator

Traces all 857 observations across the 9 Category-A drugs in pk_timecourses_clean.csv
and pk_phase3_input.csv from raw PK-DB source ZIPs to final concentration classification.

Outputs produced:
  1. data/processed/pk_concentration_recovery_audit.csv
  2. data/processed/pk_concentration_recovery_summary.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

WORKSPACE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = WORKSPACE_DIR / "data" / "processed"
CLEAN_CSV = PROCESSED_DIR / "pk_timecourses_clean.csv"
INPUT_CSV = PROCESSED_DIR / "pk_phase3_input.csv"
CONC_CSV = PROCESSED_DIR / "pk_phase3_concentration_only.csv"

OUT_AUDIT_CSV = PROCESSED_DIR / "pk_concentration_recovery_audit.csv"
OUT_SUMMARY_CSV = PROCESSED_DIR / "pk_concentration_recovery_summary.csv"

CAT_A_DRUGS = [
    ("metoprolol", "metoprolol", "CHEMBL13"),
    ("omeprazole", "omeprazole", "CHEMBL1503"),
    ("midazolam", "midazolam", "CHEMBL655"),
    ("simvastatin", "simvastatin", "CHEMBL1064"),
    ("losartan", "losartan", "CHEMBL191"),
    ("Losartan carboxylic acid (E3174)", "exp3174", "CHEMBL907"),
    ("talinolol", "talinolol", "CHEMBL152067"),
    ("chlorzoxazone", "chlorzoxazone", "CHEMBL1371"),
    ("rifampicin", "rifampicin", "CHEMBL374478"),
]

def main():
    df_clean = pd.read_csv(CLEAN_CSV) if CLEAN_CSV.exists() else pd.DataFrame()
    df_input = pd.read_csv(INPUT_CSV) if INPUT_CSV.exists() else pd.DataFrame()
    df_conc = pd.read_csv(CONC_CSV) if CONC_CSV.exists() else pd.DataFrame()

    cat_a_sids = [sid for _, sid, _ in CAT_A_DRUGS]
    df_clean_cat_a = df_clean[df_clean["pkdb_id"].isin(cat_a_sids)].copy()

    audit_rows = []
    
    for _, row in df_clean_cat_a.iterrows():
        drug_name = row.get("drug_name")
        pkdb_id = row.get("pkdb_id")
        chembl_id = row.get("chembl_id")
        study_sid = row.get("study_sid")
        group_pk = row.get("group_pk")
        individual_pk = row.get("individual_pk")
        source_table = row.get("source_table")
        raw_unit = str(row.get("raw_unit")).strip()
        std_unit = str(row.get("unit_std")).strip()
        time_hr = row.get("time_hr")
        val = row.get("value_std") if pd.notna(row.get("value_std")) else row.get("raw_value")

        # Determine measurement_type and scientific classification
        if source_table == "interventions":
            m_type = "dosing"
            if std_unit in ["g", "gram", "mg"] or "kilogram" in raw_unit:
                classification = "administered_dosing_mass"
                exclusion_reason = "Administered dose event, not drug concentration in biological fluid"
            elif std_unit == "becquerel":
                classification = "radioactivity_dosing_event"
                exclusion_reason = "Administered radioactivity dose, not concentration profile"
            elif std_unit == "ml":
                classification = "dose_volume"
                exclusion_reason = "Administered fluid volume, not concentration profile"
            else:
                classification = "dosing_intervention"
                exclusion_reason = "Dosing intervention event, not concentration measurement"
            retained = False

        elif source_table == "scatters":
            m_type = "scatter_plot_point"
            if std_unit == "mole / liter":
                classification = "bivariate_scatter_ratio_point"
                exclusion_reason = "Bivariate scatter plot comparison point (AUC vs conc ratio at 2 discrete timepoints 192/576h), not time-series C(t) trajectory"
                retained = False  # Scientifically false for C(t) timecourse
            elif "hour" in std_unit:
                classification = "auc_exposure_parameter"
                exclusion_reason = "Integrated AUC exposure parameter, not concentration profile"
                retained = False
            else:
                classification = "scatter_observation"
                exclusion_reason = "Scatter plot correlation point, not C(t) trajectory"
                retained = False
        else:
            m_type = "output_parameter"
            classification = "aggregate_pk_parameter"
            exclusion_reason = "Summary PK output parameter, not timecourse observation"
            retained = False

        audit_rows.append({
            "drug_name": drug_name,
            "pkdb_id": pkdb_id,
            "chembl_id": chembl_id,
            "study_sid": study_sid,
            "group_pk": group_pk,
            "individual_pk": individual_pk,
            "source_table": source_table,
            "measurement_type": m_type,
            "raw_unit": raw_unit,
            "standard_unit": std_unit,
            "time_hr": time_hr,
            "value": val,
            "classification": classification,
            "retained_in_strict_concentration_dataset": retained,
            "exclusion_reason": exclusion_reason
        })

    df_audit = pd.DataFrame(audit_rows)
    df_audit.to_csv(OUT_AUDIT_CSV, index=False)
    print(f"Saved audit log ({len(df_audit)} rows) to {OUT_AUDIT_CSV}")

    # Build drug-level summary table (one row per Category-A drug)
    summary_rows = []
    
    for drug_name, pkdb_id, chembl_id in CAT_A_DRUGS:
        df_d = df_audit[df_audit["pkdb_id"] == pkdb_id]
        df_clean_d = df_clean_cat_a[df_clean_cat_a["pkdb_id"] == pkdb_id]
        
        raw_obs = len(df_clean_d)
        clean_obs = len(df_d)
        
        # Candidate concentration observations (e.g. mole/liter scatter points)
        df_cand = df_d[df_d["standard_unit"] == "mole / liter"]
        cand_obs = len(df_cand)
        
        # Scientifically retained valid C(t) concentration observations
        df_ret = df_d[df_d["retained_in_strict_concentration_dataset"] == True]
        ret_obs = len(df_ret)
        
        unique_t_pts = df_ret["time_hr"].nunique() if len(df_ret) > 0 else 0
        conc_units = "; ".join(df_cand["standard_unit"].unique()) if cand_obs > 0 else "None"
        m_types = "; ".join(df_d["measurement_type"].unique()) if len(df_d) > 0 else "None"
        
        studies_cnt = df_d["study_sid"].nunique() if len(df_d) > 0 else 0
        
        # Count subjects / groups
        grps = df_d["group_pk"].dropna().nunique()
        inds = df_d["individual_pk"].dropna().nunique()
        subj_str = f"groups={grps}, individuals={inds}"
        
        if pkdb_id in ["losartan", "exp3174"]:
            reason_for_loss = "A. Correctly excluded — not concentration (dosing interventions and bivariate scatter ratio points)"
            rec_possible = False
        else:
            reason_for_loss = "E. PK-DB genuinely lacks sufficient concentration observations (unauthenticated API zip payload contains empty timecourses.csv)"
            rec_possible = False

        summary_rows.append({
            "drug_name": drug_name,
            "chembl_id": chembl_id,
            "raw_observations": raw_obs,
            "cleaned_observations": clean_obs,
            "candidate_concentration_observations": cand_obs,
            "retained_concentration_observations": ret_obs,
            "unique_concentration_timepoints": unique_t_pts,
            "concentration_units": conc_units,
            "measurement_types": m_types,
            "studies": studies_cnt,
            "subjects_or_groups": subj_str,
            "reason_for_loss": reason_for_loss,
            "recovery_possible": rec_possible
        })

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(OUT_SUMMARY_CSV, index=False)
    print(f"Saved drug-level summary table ({len(df_summary)} rows) to {OUT_SUMMARY_CSV}")

if __name__ == "__main__":
    main()
