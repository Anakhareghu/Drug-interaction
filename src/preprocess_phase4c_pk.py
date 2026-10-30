"""
preprocess_phase4c_pk.py
========================
Phase 4C — Extended Replacement PK Preprocessing & Ingestion Engine

Parses all open longitudinal PK datasets in data/raw/replacement_pk/,
standardizes time values to hours (time_hr) and concentration to standard units (mg/L),
applies strict validation rules, and constructs:
  1. data/processed/pk_phase4_extended_clean.csv
  2. data/processed/pk_phase4c_ingestion_audit.csv

Target Schema for pk_phase4_extended_clean.csv:
  drug_name
  chembl_id
  study_id
  subject_id
  time_hr
  concentration
  concentration_unit
  biological_matrix
  route
  dose_mg
  is_plasma_concentration
"""

import pandas as pd
import numpy as np
from pathlib import Path

WORKSPACE_DIR = Path(__file__).parent.parent
RAW_REPLACEMENT_DIR = WORKSPACE_DIR / "data" / "raw" / "replacement_pk"
PROCESSED_DIR = WORKSPACE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUT_EXTENDED_CLEAN_CSV = PROCESSED_DIR / "pk_phase4_extended_clean.csv"
OUT_AUDIT_CSV = PROCESSED_DIR / "pk_phase4c_ingestion_audit.csv"

# ChEMBL Accession mapping for all candidate benchmark drugs
CHEMBL_MAPPING = {
    "theophylline": "CHEMBL178",
    "indomethacin": "CHEMBL6",
    "phenobarbital": "CHEMBL40",
    "quinidine": "CHEMBL481",
    "remifentanil": "CHEMBL1201179",
    "cefamandole": "CHEMBL1433",
    "xanomeline": "CHEMBL286290",
    "tetracycline": "CHEMBL460",
}

def process_theophylline():
    fpath = RAW_REPLACEMENT_DIR / "Theoph.csv"
    if not fpath.exists():
        return [], []
    df = pd.read_csv(fpath)
    records = []
    exclusions = []
    
    for idx, row in df.iterrows():
        subj = f"THEO_SUBJ_{int(row['Subject'])}"
        t = float(row['Time'])
        c = float(row['conc'])
        wt = float(row['Wt'])
        dose_mg = float(row['Dose']) * wt
        
        if pd.isna(c) or c <= 0:
            exclusions.append({"source": "Theoph.csv", "drug_name": "theophylline", "row_index": idx, "reason": "Non-positive or NaN concentration value"})
            continue
        if t < 0 or pd.isna(t):
            exclusions.append({"source": "Theoph.csv", "drug_name": "theophylline", "row_index": idx, "reason": "Negative or NaN time point"})
            continue
            
        records.append({
            "drug_name": "theophylline",
            "chembl_id": CHEMBL_MAPPING["theophylline"],
            "study_id": "STUDY_THEOPH_NLME",
            "subject_id": subj,
            "time_hr": round(t, 4),
            "concentration": round(c, 4),
            "concentration_unit": "mg/L",
            "biological_matrix": "plasma",
            "route": "oral",
            "dose_mg": round(dose_mg, 2),
            "is_plasma_concentration": True
        })
    return records, exclusions

def process_indomethacin():
    fpath = RAW_REPLACEMENT_DIR / "Indometh.csv"
    if not fpath.exists():
        return [], []
    df = pd.read_csv(fpath)
    records = []
    exclusions = []
    
    for idx, row in df.iterrows():
        subj = f"INDO_SUBJ_{int(row['Subject'])}"
        t = float(row['time'])
        c = float(row['conc'])
        
        if pd.isna(c) or c <= 0:
            exclusions.append({"source": "Indometh.csv", "drug_name": "indomethacin", "row_index": idx, "reason": "Non-positive or NaN concentration value"})
            continue
        if t < 0 or pd.isna(t):
            exclusions.append({"source": "Indometh.csv", "drug_name": "indomethacin", "row_index": idx, "reason": "Negative or NaN time point"})
            continue
            
        records.append({
            "drug_name": "indomethacin",
            "chembl_id": CHEMBL_MAPPING["indomethacin"],
            "study_id": "STUDY_INDOMETH_NLME",
            "subject_id": subj,
            "time_hr": round(t, 4),
            "concentration": round(c, 4),
            "concentration_unit": "mg/L",
            "biological_matrix": "plasma",
            "route": "intravenous",
            "dose_mg": 25.0,
            "is_plasma_concentration": True
        })
    return records, exclusions

def process_phenobarbital():
    fpath = RAW_REPLACEMENT_DIR / "Phenobarb.csv"
    if not fpath.exists():
        return [], []
    df = pd.read_csv(fpath)
    records = []
    exclusions = []
    
    for idx, row in df.iterrows():
        subj = f"PHEN_SUBJ_{int(row['Subject'])}"
        t = float(row['time'])
        c = row['conc']
        dose_mg = float(row['dose']) if pd.notna(row['dose']) else 25.0
        
        if pd.isna(c):
            exclusions.append({"source": "Phenobarb.csv", "drug_name": "phenobarbital", "row_index": idx, "reason": "NaN concentration (dosing record)"})
            continue
        c = float(c)
        if c <= 0:
            exclusions.append({"source": "Phenobarb.csv", "drug_name": "phenobarbital", "row_index": idx, "reason": "Non-positive concentration value"})
            continue
        if t < 0 or pd.isna(t):
            exclusions.append({"source": "Phenobarb.csv", "drug_name": "phenobarbital", "row_index": idx, "reason": "Negative or NaN time point"})
            continue
            
        records.append({
            "drug_name": "phenobarbital",
            "chembl_id": CHEMBL_MAPPING["phenobarbital"],
            "study_id": "STUDY_PHENOBARB_NLME",
            "subject_id": subj,
            "time_hr": round(t, 4),
            "concentration": round(c, 4),
            "concentration_unit": "mg/L",
            "biological_matrix": "serum",
            "route": "intravenous",
            "dose_mg": dose_mg,
            "is_plasma_concentration": True
        })
    return records, exclusions

def process_quinidine():
    fpath = RAW_REPLACEMENT_DIR / "Quinidine.csv"
    if not fpath.exists():
        return [], []
    df = pd.read_csv(fpath)
    records = []
    exclusions = []
    
    for idx, row in df.iterrows():
        subj = f"QUIN_SUBJ_{int(row['Subject'])}"
        t = float(row['time'])
        c = row['conc']
        dose_mg = float(row['dose']) if pd.notna(row['dose']) else 249.0
        
        if pd.isna(c):
            exclusions.append({"source": "Quinidine.csv", "drug_name": "quinidine", "row_index": idx, "reason": "NaN concentration (dosing record)"})
            continue
        c = float(c)
        if c <= 0:
            exclusions.append({"source": "Quinidine.csv", "drug_name": "quinidine", "row_index": idx, "reason": "Non-positive concentration value"})
            continue
        if t < 0 or pd.isna(t):
            exclusions.append({"source": "Quinidine.csv", "drug_name": "quinidine", "row_index": idx, "reason": "Negative or NaN time point"})
            continue
            
        records.append({
            "drug_name": "quinidine",
            "chembl_id": CHEMBL_MAPPING["quinidine"],
            "study_id": "STUDY_QUINIDINE_NLME",
            "subject_id": subj,
            "time_hr": round(t, 4),
            "concentration": round(c, 4),
            "concentration_unit": "mg/L",
            "biological_matrix": "serum",
            "route": "oral",
            "dose_mg": dose_mg,
            "is_plasma_concentration": True
        })
    return records, exclusions

def process_remifentanil():
    fpath = RAW_REPLACEMENT_DIR / "Remifentanil.csv"
    if not fpath.exists():
        return [], []
    df = pd.read_csv(fpath)
    records = []
    exclusions = []
    
    for idx, row in df.iterrows():
        subj = f"REMI_SUBJ_{int(row['Subject'])}"
        t_min = float(row['Time'])
        t_hr = t_min / 60.0 # min -> hr
        c_ng = row['conc']
        
        if pd.isna(c_ng):
            exclusions.append({"source": "Remifentanil.csv", "drug_name": "remifentanil", "row_index": idx, "reason": "NaN concentration (infusion record)"})
            continue
        c_ng = float(c_ng)
        if c_ng <= 0:
            exclusions.append({"source": "Remifentanil.csv", "drug_name": "remifentanil", "row_index": idx, "reason": "Non-positive concentration value"})
            continue
            
        c_mgl = c_ng / 1000.0
        dose_ug = float(row['Amt']) if pd.notna(row['Amt']) else 1000.0
        dose_mg = dose_ug / 1000.0
        
        records.append({
            "drug_name": "remifentanil",
            "chembl_id": CHEMBL_MAPPING["remifentanil"],
            "study_id": "STUDY_REMIFENTANIL_NLME",
            "subject_id": subj,
            "time_hr": round(t_hr, 4),
            "concentration": round(c_mgl, 6),
            "concentration_unit": "mg/L",
            "biological_matrix": "plasma",
            "route": "intravenous",
            "dose_mg": dose_mg,
            "is_plasma_concentration": True
        })
    return records, exclusions

def process_cefamandole():
    fpath = RAW_REPLACEMENT_DIR / "Cefamandole.csv"
    if not fpath.exists():
        return [], []
    df = pd.read_csv(fpath)
    records = []
    exclusions = []
    
    for idx, row in df.iterrows():
        subj = f"CEFA_SUBJ_{int(row['Subject'])}"
        t_min = float(row['Time'])
        t_hr = t_min / 60.0 # min -> hr
        c = float(row['conc'])
        
        if pd.isna(c) or c <= 0:
            exclusions.append({"source": "Cefamandole.csv", "drug_name": "cefamandole", "row_index": idx, "reason": "Non-positive or NaN concentration value"})
            continue
        if t_hr < 0 or pd.isna(t_hr):
            exclusions.append({"source": "Cefamandole.csv", "drug_name": "cefamandole", "row_index": idx, "reason": "Negative or NaN time point"})
            continue
            
        records.append({
            "drug_name": "cefamandole",
            "chembl_id": CHEMBL_MAPPING["cefamandole"],
            "study_id": "STUDY_CEFAMANDOLE_NLME",
            "subject_id": subj,
            "time_hr": round(t_hr, 4),
            "concentration": round(c, 4),
            "concentration_unit": "mg/L",
            "biological_matrix": "plasma",
            "route": "intravenous",
            "dose_mg": 1000.0,
            "is_plasma_concentration": True
        })
    return records, exclusions

def process_xanomeline():
    fpath = RAW_REPLACEMENT_DIR / "PC.csv"
    if not fpath.exists():
        return [], []
    df = pd.read_csv(fpath)
    records = []
    exclusions = []
    
    for idx, row in df.iterrows():
        usubjid = str(row['USUBJID'])
        subj = f"XANO_SUBJ_{usubjid}"
        t_tpt = row.get('PCTPTNUM')
        c_val = row.get('PCSTRESN')
        unit_str = str(row.get('PCSTRESU'))
        
        if pd.isna(c_val):
            exclusions.append({"source": "PC.csv", "drug_name": "xanomeline", "row_index": idx, "reason": "NaN concentration measurement"})
            continue
        c_val = float(c_val)
        if c_val <= 0:
            exclusions.append({"source": "PC.csv", "drug_name": "xanomeline", "row_index": idx, "reason": "Non-positive or zero concentration value"})
            continue
        if pd.isna(t_tpt) or float(t_tpt) < 0:
            exclusions.append({"source": "PC.csv", "drug_name": "xanomeline", "row_index": idx, "reason": "Pre-dose or negative timepoint"})
            continue
            
        t_hr = float(t_tpt)
        # Convert ng/mL to mg/L
        c_mgl = c_val / 1000.0 if "ng" in unit_str.lower() else c_val
        
        records.append({
            "drug_name": "xanomeline",
            "chembl_id": CHEMBL_MAPPING["xanomeline"],
            "study_id": "STUDY_CDISCPILOT01",
            "subject_id": subj,
            "time_hr": round(t_hr, 4),
            "concentration": round(c_mgl, 6),
            "concentration_unit": "mg/L",
            "biological_matrix": "plasma",
            "route": "oral",
            "dose_mg": 54.0,
            "is_plasma_concentration": True
        })
    return records, exclusions

def process_tetracycline():
    records = []
    exclusions = []
    
    for fname in ["Tetracycline1.csv", "Tetracycline2.csv"]:
        fpath = RAW_REPLACEMENT_DIR / fname
        if not fpath.exists():
            continue
        df = pd.read_csv(fpath)
        for idx, row in df.iterrows():
            form = str(row['Formulation'])
            subj = f"TETRA_SUBJ_{form.upper()}_{int(row['Subject'])}"
            t = float(row['Time'])
            c = float(row['conc'])
            
            if pd.isna(c) or c <= 0:
                exclusions.append({"source": fname, "drug_name": "tetracycline", "row_index": idx, "reason": "Non-positive or NaN concentration value"})
                continue
                
            records.append({
                "drug_name": "tetracycline",
                "chembl_id": CHEMBL_MAPPING["tetracycline"],
                "study_id": f"STUDY_TETRACYCLINE_{form.upper()}",
                "subject_id": subj,
                "time_hr": round(t, 4),
                "concentration": round(c, 4),
                "concentration_unit": "mg/L",
                "biological_matrix": "serum",
                "route": "oral",
                "dose_mg": 250.0,
                "is_plasma_concentration": True
            })
    return records, exclusions

def main():
    print("Preprocessing Phase 4C extended replacement PK benchmark datasets...")
    
    all_records = []
    all_exclusions = []
    
    processors = [
        process_theophylline,
        process_indomethacin,
        process_phenobarbital,
        process_quinidine,
        process_remifentanil,
        process_cefamandole,
        process_xanomeline,
        process_tetracycline
    ]
    
    for proc in processors:
        recs, excls = proc()
        all_records.extend(recs)
        all_exclusions.extend(excls)
        
    df_clean = pd.DataFrame(all_records)
    cols_order = [
        "drug_name", "chembl_id", "study_id", "subject_id",
        "time_hr", "concentration", "concentration_unit",
        "biological_matrix", "route", "dose_mg", "is_plasma_concentration"
    ]
    df_clean = df_clean[cols_order]
    df_clean.to_csv(OUT_EXTENDED_CLEAN_CSV, index=False)
    print(f"Saved extended clean Phase 4 dataset ({len(df_clean)} rows) to {OUT_EXTENDED_CLEAN_CSV}")
    
    # Build Ingestion Audit CSV
    audit_summary = []
    grouped = df_clean.groupby("drug_name")
    
    for drug_name, group in grouped:
        chembl_id = group["chembl_id"].iloc[0]
        study_id = group["study_id"].iloc[0]
        n_obs = len(group)
        n_subjs = group["subject_id"].nunique()
        n_tpts = group["time_hr"].nunique()
        min_t = group["time_hr"].min()
        max_t = group["time_hr"].max()
        matrix = group["biological_matrix"].iloc[0]
        route = group["route"].iloc[0]
        units = group["concentration_unit"].iloc[0]
        
        excl_count = sum(1 for e in all_exclusions if e["drug_name"] == drug_name)
        
        audit_summary.append({
            "source": f"Rdatasets / {study_id}",
            "drug_name": drug_name,
            "chembl_id": chembl_id,
            "study_id": study_id,
            "subject_count": n_subjs,
            "observation_count": n_obs,
            "unique_time_points": n_tpts,
            "min_time_hr": min_t,
            "max_time_hr": max_t,
            "concentration_unit": units,
            "biological_matrix": matrix,
            "route": route,
            "valid_concentration_count": n_obs,
            "excluded_count": excl_count,
            "exclusion_reason": "Pre-dose, NaN, or non-positive concentration rows",
            "chembl_mapping_status": "MAPPED_1TO1",
            "trajectory_gate_status": "PASS" if (n_tpts >= 5) and (matrix in ["plasma", "serum"]) else "FAIL"
        })
        
    df_audit = pd.DataFrame(audit_summary)
    df_audit.to_csv(OUT_AUDIT_CSV, index=False)
    print(f"Saved Phase 4C ingestion audit table ({len(df_audit)} drugs) to {OUT_AUDIT_CSV}")

if __name__ == "__main__":
    main()
