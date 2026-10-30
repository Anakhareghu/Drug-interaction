"""
preprocess_pk.py
================
Phase 2 — PK Time-Series Preprocessing Engine

Executes the Phase 2 PK time-series data acquisition, standardization,
cleaning, and quality control pipeline for the 36 usable drugs from Phase 1.

Tasks performed:
  1. Retrieve raw PK observation records (scatters, outputs, interventions) for usable drugs.
  2. Preserve original time and concentration values/units (raw_time, raw_time_unit, raw_value, raw_unit).
  3. Convert time to standardized hours (time_hr) unambiguously (hr, min, day, week).
  4. Standardize concentration units (value_std, unit_std) where conversion is unambiguous, preserving dimensionless/normalized values.
  5. Remove invalid/missing records (negative time, non-positive values, NaNs).
  6. Maintain full granularity (study_sid, group_pk, individual_pk) without merging across entities.
  7. Generate dataset outputs:
     - data/processed/pk_timecourses_clean.csv
     - data/processed/pk_preprocessing_summary.csv

Usage:
    python src/preprocess_pk.py
"""

import os
import json
import zipfile
import io
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

BASE_URL = "https://pk-db.com/api/v1"
WORKSPACE_DIR = Path(__file__).parent.parent
RAW_PKDB_DIR = WORKSPACE_DIR / "data" / "raw" / "pkdb"
PROCESSED_DIR = WORKSPACE_DIR / "data" / "processed"
CANDIDATE_SUMMARY = PROCESSED_DIR / "pkdb_chembl_candidate_summary.csv"

RAW_PKDB_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Unit Standardization Rules
# ---------------------------------------------------------------------------

TIME_UNIT_CONVERSION = {
    "hr": 1.0,
    "hour": 1.0,
    "hours": 1.0,
    "h": 1.0,
    "min": 1/60.0,
    "minute": 1/60.0,
    "minutes": 1/60.0,
    "day": 24.0,
    "days": 24.0,
    "d": 24.0,
    "week": 168.0,
    "weeks": 168.0,
    "w": 168.0,
}

CONC_UNIT_CONVERSION = {
    "mg/l": (1.0, "mg/L"),
    "mg/liter": (1.0, "mg/L"),
    "ug/ml": (1.0, "mg/L"),
    "g/m3": (1.0, "mg/L"),
    "ug/l": (1.0, "ug/L"),
    "ug/liter": (1.0, "ug/L"),
    "ng/ml": (1.0, "ug/L"),
    "mg/m3": (1.0, "ug/L"),
    "ng/l": (1.0, "ng/L"),
    "pg/ml": (1.0, "ng/L"),
    "nmol/l": (1.0, "nmol/L"),
    "umol/l": (1.0, "umol/L"),
    "gram": (1.0, "g"),
    "g": (1.0, "g"),
    "mg": (0.001, "g"),
}

def standardize_time(val, unit):
    if pd.isna(val) or pd.isna(unit):
        return np.nan
    unit_clean = str(unit).strip().lower()
    factor = TIME_UNIT_CONVERSION.get(unit_clean)
    if factor is not None:
        try:
            return float(val) * factor
        except (ValueError, TypeError):
            return np.nan
    return np.nan

def standardize_conc(val, unit):
    if pd.isna(val):
        return np.nan, "missing"
    try:
        fval = float(val)
    except (ValueError, TypeError):
        return np.nan, "invalid"
        
    if pd.isna(unit):
        return fval, "unspecified"
        
    unit_clean = str(unit).strip().lower()
    conv = CONC_UNIT_CONVERSION.get(unit_clean)
    if conv is not None:
        factor, std_unit = conv
        return fval * factor, std_unit
    return fval, str(unit).strip()


def parse_array_or_val(val):
    """Parse JSON string array or numeric value."""
    if isinstance(val, str) and val.strip().startswith("["):
        try:
            return json.loads(val)
        except Exception:
            return []
    elif pd.notna(val):
        try:
            return [float(val)]
        except Exception:
            return []
    return []


def extract_drug_records(sid, label, chembl_id):
    """
    Fetch / load raw ZIP archive for a drug and extract all measurement observations.
    Returns list of dict observation records.
    """
    zip_path = RAW_PKDB_DIR / f"raw_filter_{sid}.zip"
    
    if not zip_path.exists():
        params = {"studies__substance": sid, "download": "true"}
        try:
            r = requests.get(f"{BASE_URL}/filter/", params=params, timeout=45)
            if r.status_code == 200 and 'zip' in r.headers.get("content-type", ""):
                with open(zip_path, "wb") as f:
                    f.write(r.content)
        except Exception as e:
            print(f"Warning downloading ZIP for {sid}: {e}")
            
    observations = []
    
    if zip_path.exists():
        try:
            z = zipfile.ZipFile(zip_path)
            
            # 1. Scatters (paired x/y observations)
            if "scatters.csv" in z.namelist():
                content = z.read("scatters.csv").decode("utf-8", errors="replace")
                if len(content.strip()) > 10:
                    df_scat = pd.read_csv(io.StringIO(content))
                    for _, row in df_scat.iterrows():
                        study_sid = row.get("study_sid")
                        
                        # Case A: x is time, y is concentration/value
                        x_t_arr = parse_array_or_val(row.get("x_time"))
                        y_v_arr = parse_array_or_val(row.get("y_value"))
                        x_unit = row.get("x_time_unit") or row.get("x_unit")
                        y_unit = row.get("y_unit")
                        g_pk = row.get("x_group_pk") or row.get("y_group_pk")
                        i_pk = row.get("x_individual_pk") or row.get("y_individual_pk")
                        
                        if len(x_t_arr) > 0 and len(y_v_arr) > 0:
                            for t_item, v_item in zip(x_t_arr, y_v_arr):
                                observations.append({
                                    "drug_name": label,
                                    "pkdb_id": sid,
                                    "chembl_id": chembl_id,
                                    "study_sid": study_sid,
                                    "group_pk": g_pk,
                                    "individual_pk": i_pk,
                                    "raw_time": t_item,
                                    "raw_time_unit": x_unit,
                                    "raw_value": v_item,
                                    "raw_unit": y_unit,
                                    "source_table": "scatters",
                                })
                                
                        # Case B: y is time, x is concentration/value
                        y_t_arr = parse_array_or_val(row.get("y_time"))
                        x_v_arr = parse_array_or_val(row.get("x_value"))
                        if len(y_t_arr) > 0 and len(x_v_arr) > 0 and len(x_t_arr) == 0:
                            y_t_unit = row.get("y_time_unit") or row.get("y_unit")
                            x_v_unit = row.get("x_unit")
                            for t_item, v_item in zip(y_t_arr, x_v_arr):
                                observations.append({
                                    "drug_name": label,
                                    "pkdb_id": sid,
                                    "chembl_id": chembl_id,
                                    "study_sid": study_sid,
                                    "group_pk": g_pk,
                                    "individual_pk": i_pk,
                                    "raw_time": t_item,
                                    "raw_time_unit": y_t_unit,
                                    "raw_value": v_item,
                                    "raw_unit": x_v_unit,
                                    "source_table": "scatters",
                                })

            # 2. Interventions (dosing timepoints)
            if "interventions.csv" in z.namelist():
                content = z.read("interventions.csv").decode("utf-8", errors="replace")
                if len(content.strip()) > 10:
                    df_int = pd.read_csv(io.StringIO(content))
                    for _, row in df_int.iterrows():
                        t_val = row.get("time")
                        v_val = row.get("value")
                        if pd.notna(t_val) and pd.notna(v_val):
                            observations.append({
                                "drug_name": label,
                                "pkdb_id": sid,
                                "chembl_id": chembl_id,
                                "study_sid": row.get("study_sid"),
                                "group_pk": np.nan,
                                "individual_pk": np.nan,
                                "raw_time": t_val,
                                "raw_time_unit": row.get("time_unit"),
                                "raw_value": v_val,
                                "raw_unit": row.get("unit"),
                                "source_table": "interventions",
                            })

            # 3. Outputs
            if "outputs.csv" in z.namelist():
                content = z.read("outputs.csv").decode("utf-8", errors="replace")
                if len(content.strip()) > 10:
                    df_out = pd.read_csv(io.StringIO(content))
                    for _, row in df_out.iterrows():
                        t_val = row.get("time")
                        v_val = row.get("value") or row.get("mean")
                        if pd.notna(t_val) and pd.notna(v_val):
                            observations.append({
                                "drug_name": label,
                                "pkdb_id": sid,
                                "chembl_id": chembl_id,
                                "study_sid": row.get("study_sid"),
                                "group_pk": row.get("group_pk"),
                                "individual_pk": row.get("individual_pk"),
                                "raw_time": t_val,
                                "raw_time_unit": row.get("time_unit"),
                                "raw_value": v_val,
                                "raw_unit": row.get("unit"),
                                "source_table": "outputs",
                            })

        except Exception as e:
            print(f"Error parsing ZIP for {sid}: {e}")
            
    return observations


def main():
    print("==================== PHASE 2: PK TIME-SERIES PREPROCESSING ENGINE ====================")
    df_candidates = pd.read_csv(CANDIDATE_SUMMARY)
    usable_drugs = df_candidates[df_candidates["status"] == "usable"].copy()
    print(f"Processing {len(usable_drugs)} usable drugs...")
    
    all_clean_records = []
    summary_stats = []
    
    for _, row in tqdm(usable_drugs.iterrows(), total=len(usable_drugs), desc="Processing PK data"):
        sid = row["pkdb_id"]
        label = row["drug_name"]
        chembl_id = row["chembl_id"]
        
        raw_obs = extract_drug_records(sid, label, chembl_id)
        total_raw = len(raw_obs)
        
        if total_raw == 0:
            summary_stats.append({
                "drug_name": label,
                "pkdb_id": sid,
                "chembl_id": chembl_id,
                "total_raw_obs": 0,
                "cleaned_obs": 0,
                "invalid_removed": 0,
                "time_conversions": 0,
                "conc_conversions": 0,
                "unique_studies": 0,
                "unique_groups": 0,
                "unique_individuals": 0,
                "min_time_hr": np.nan,
                "max_time_hr": np.nan,
                "status": "no_raw_records",
            })
            continue
            
        df_obs = pd.DataFrame(raw_obs)
        
        # Standardize time
        df_obs["time_hr"] = df_obs.apply(lambda r: standardize_time(r["raw_time"], r["raw_time_unit"]), axis=1)
        
        # Standardize concentration
        std_conc_res = df_obs.apply(lambda r: standardize_conc(r["raw_value"], r["raw_unit"]), axis=1)
        df_obs["value_std"] = [res[0] for res in std_conc_res]
        df_obs["unit_std"] = [res[1] for res in std_conc_res]
        
        time_conv_cnt = df_obs["time_hr"].notna().sum()
        conc_conv_cnt = df_obs["value_std"].notna().sum()
        
        # Quality filtering rules:
        # 1. Remove missing / NaN time_hr or value_std
        # 2. Remove negative time (time_hr < 0)
        # 3. Remove non-positive concentration values (value_std <= 0)
        valid_mask = (
            df_obs["time_hr"].notna() &
            df_obs["value_std"].notna() &
            (df_obs["time_hr"] >= 0) &
            (df_obs["value_std"] > 0)
        )
        
        df_clean = df_obs[valid_mask].copy()
        cleaned_cnt = len(df_clean)
        removed_cnt = total_raw - cleaned_cnt
        
        if cleaned_cnt > 0:
            all_clean_records.append(df_clean)
            
            n_studies = df_clean["study_sid"].nunique()
            n_groups = df_clean["group_pk"].nunique()
            n_indiv = df_clean["individual_pk"].nunique()
            min_t = df_clean["time_hr"].min()
            max_t = df_clean["time_hr"].max()
            
            summary_stats.append({
                "drug_name": label,
                "pkdb_id": sid,
                "chembl_id": chembl_id,
                "total_raw_obs": total_raw,
                "cleaned_obs": cleaned_cnt,
                "invalid_removed": removed_cnt,
                "time_conversions": time_conv_cnt,
                "conc_conversions": conc_conv_cnt,
                "unique_studies": n_studies,
                "unique_groups": n_groups,
                "unique_individuals": n_indiv,
                "min_time_hr": round(float(min_t), 2),
                "max_time_hr": round(float(max_t), 2),
                "status": "processed",
            })
        else:
            summary_stats.append({
                "drug_name": label,
                "pkdb_id": sid,
                "chembl_id": chembl_id,
                "total_raw_obs": total_raw,
                "cleaned_obs": 0,
                "invalid_removed": removed_cnt,
                "time_conversions": time_conv_cnt,
                "conc_conversions": conc_conv_cnt,
                "unique_studies": 0,
                "unique_groups": 0,
                "unique_individuals": 0,
                "min_time_hr": np.nan,
                "max_time_hr": np.nan,
                "status": "all_filtered",
            })

    # Combine all cleaned timecourses
    if all_clean_records:
        df_all_clean = pd.concat(all_clean_records, ignore_index=True)
        
        cols_order = [
            "drug_name", "pkdb_id", "chembl_id", "study_sid",
            "group_pk", "individual_pk", "time_hr", "value_std",
            "unit_std", "raw_time", "raw_time_unit", "raw_value",
            "raw_unit", "source_table"
        ]
        df_all_clean = df_all_clean[cols_order]
        
        out_clean_path = PROCESSED_DIR / "pk_timecourses_clean.csv"
        df_all_clean.to_csv(out_clean_path, index=False)
        print(f"\nSaved cleaned timecourses ({len(df_all_clean)} observations across {df_all_clean['drug_name'].nunique()} drugs) to {out_clean_path}")
        
    df_summary = pd.DataFrame(summary_stats)
    out_sum_path = PROCESSED_DIR / "pk_preprocessing_summary.csv"
    df_summary.to_csv(out_sum_path, index=False)
    print(f"Saved preprocessing summary ({len(df_summary)} drugs) to {out_sum_path}")

if __name__ == "__main__":
    main()
