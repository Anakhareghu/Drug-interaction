"""
prepare_phase5_modeling_matrix.py
==================================
Phase 5A — Modeling Matrix Preparation and Preprocessing Engine

Converts validated subject-level PK observations into scientifically defensible,
dose-normalized and peak-normalized 7x15 drug-level trajectory matrices for downstream SVD/DMD.

Stages:
  Stage 1: Input Validation
  Stage 2: Subject-Level Trajectory Construction
  Stage 3: T=0 Handling
  Stage 4: Dose Normalization
  Stage 5: Peak Normalization
  Stage 6: Standard Time Grid Interpolation (15 points: 0 - 24 hr)
  Stage 7: Subject -> Drug Aggregation & Uncertainty Audit
  Stage 8: Candidate Matrix Validation & Output Export

Usage:
    python src/prepare_phase5_modeling_matrix.py
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.interpolate import PchipInterpolator

WORKSPACE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = WORKSPACE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CLEAN_CSV = PROCESSED_DIR / "pk_phase4_extended_clean.csv"

OUT_SUBJECT_TRAJ_CSV = PROCESSED_DIR / "pk_phase5_subject_trajectories.csv"
OUT_DRUG_MEAN_TRAJ_CSV = PROCESSED_DIR / "pk_phase5_drug_mean_trajectories.csv"
OUT_DOSE_NORM_MATRIX_CSV = PROCESSED_DIR / "pk_phase5_dose_normalized_matrix.csv"
OUT_PEAK_NORM_MATRIX_CSV = PROCESSED_DIR / "pk_phase5_peak_normalized_matrix.csv"
OUT_STATISTICS_CSV = PROCESSED_DIR / "pk_phase5_trajectory_statistics.csv"
OUT_AUDIT_CSV = PROCESSED_DIR / "pk_phase5_preprocessing_audit.csv"

VALIDATED_DRUGS = ["cefamandole", "indomethacin", "phenobarbital", "quinidine", "remifentanil", "theophylline", "xanomeline"]

# 15-point standard temporal evaluation grid (in hours) spanning 0.0 to 24.0 h
T_GRID = np.array([0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0, 24.0])

def run_phase5a_pipeline():
    print("=== PHASE 5A: PREPARING MODELING MATRICES ===")
    
    audit_logs = []
    
    # ----------------------------------------------------
    # STAGE 1: INPUT VALIDATION
    # ----------------------------------------------------
    print("\n[STAGE 1] Validating Input Dataset...")
    if not INPUT_CLEAN_CSV.exists():
        raise FileNotFoundError(f"Input file {INPUT_CLEAN_CSV} not found!")
        
    df_raw = pd.read_csv(INPUT_CLEAN_CSV)
    required_cols = [
        "drug_name", "chembl_id", "study_id", "subject_id",
        "time_hr", "concentration", "concentration_unit",
        "biological_matrix", "route", "dose_mg", "is_plasma_concentration"
    ]
    for col in required_cols:
        if col not in df_raw.columns:
            raise KeyError(f"Missing required column {col} in {INPUT_CLEAN_CSV}")
            
    df_valid = df_raw[df_raw["drug_name"].isin(VALIDATED_DRUGS)].copy()
    
    # Filter numeric & valid concentration values
    initial_count = len(df_valid)
    df_clean = df_valid[
        (df_valid["concentration"].notna()) &
        (df_valid["concentration"] > 0) &
        (df_valid["time_hr"].notna()) &
        (df_valid["time_hr"] >= 0) &
        (df_valid["is_plasma_concentration"] == True) &
        (df_valid["biological_matrix"].isin(["plasma", "serum"]))
    ].copy()
    
    excl_count = initial_count - len(df_clean)
    audit_logs.append({
        "stage": "Stage 1 Input Validation",
        "transformation": "Filtered non-positive concentration and invalid time records",
        "records_retained": len(df_clean),
        "records_excluded": excl_count,
        "notes": "Retained 100% measured plasma/serum concentration records across 7 validated drugs"
    })
    print(f"  Retained {len(df_clean)} valid concentration observations ({excl_count} excluded).")

    # ----------------------------------------------------
    # STAGE 2: SUBJECT-LEVEL TRAJECTORY CONSTRUCTION
    # ----------------------------------------------------
    print("\n[STAGE 2] Constructing Subject-Level Trajectories...")
    subject_grid_records = []
    
    grouped = df_clean.groupby(["drug_name", "study_id", "subject_id"])
    subject_counts = len(grouped)
    
    for (drug, study_id, subj_id), group in grouped:
        sub_df = group.sort_values("time_hr").copy()
        
        # Average duplicates at identical timepoints
        sub_df = sub_df.groupby("time_hr").agg({
            "concentration": "mean",
            "dose_mg": "first",
            "biological_matrix": "first",
            "route": "first",
            "chembl_id": "first"
        }).reset_index()
        
        times = sub_df["time_hr"].values
        concs = sub_df["concentration"].values
        dose = float(sub_df["dose_mg"].iloc[0])
        chembl_id = str(sub_df["chembl_id"].iloc[0])
        route = str(sub_df["route"].iloc[0])
        matrix = str(sub_df["biological_matrix"].iloc[0])
        
        if len(times) < 1:
            continue
            
        cmax = float(np.max(concs))
        
        # ----------------------------------------------------
        # STAGE 3, 4, 5, 6: INTERPOLATION, DOSE & PEAK NORMALIZATION
        # ----------------------------------------------------
        c_interp = np.zeros(len(T_GRID))
        
        if len(times) == 1:
            c_interp[:] = concs[0]
        else:
            interp_func = PchipInterpolator(times, concs, extrapolate=False)
            for i, t_target in enumerate(T_GRID):
                if t_target < times[0]:
                    # STAGE 3: t=0 handling. For oral drugs without pre-dose, C(0)=0; otherwise initial measurement
                    if route == "oral" and t_target == 0:
                        c_interp[i] = 0.0
                    else:
                        c_interp[i] = concs[0]
                elif t_target > times[-1]:
                    # Short-acting drugs (remifentanil < 4h, cefamandole < 6h) reach terminal clearance C=0
                    if times[-1] < 10.0 and concs[-1] < (0.1 * cmax):
                        c_interp[i] = 0.0
                    else:
                        c_interp[i] = concs[-1]
                else:
                    val = interp_func(t_target)
                    c_interp[i] = max(0.0, float(val))
                    
        for i, t_val in enumerate(T_GRID):
            c_val = float(c_interp[i])
            # STAGE 4: Dose normalization C_norm = C / Dose
            c_norm = c_val / dose if dose > 0 else np.nan
            # STAGE 5: Peak normalization C_peak = C / Cmax
            c_peak = c_val / cmax if cmax > 0 else np.nan
            
            subject_grid_records.append({
                "drug_name": drug,
                "chembl_id": chembl_id,
                "study_id": study_id,
                "subject_id": subj_id,
                "time_hr": round(t_val, 4),
                "concentration": round(c_val, 6),
                "dose_norm_conc": round(c_norm, 8) if pd.notna(c_norm) else np.nan,
                "peak_norm_conc": round(c_peak, 6) if pd.notna(c_peak) else np.nan,
                "dose_mg": dose,
                "cmax_subject": cmax,
                "biological_matrix": matrix,
                "route": route
            })

    df_subj_grid = pd.DataFrame(subject_grid_records)
    df_subj_grid.to_csv(OUT_SUBJECT_TRAJ_CSV, index=False)
    print(f"  Saved subject-level grid trajectories ({len(df_subj_grid)} rows across {df_subj_grid['subject_id'].nunique()} subjects) to {OUT_SUBJECT_TRAJ_CSV}")

    audit_logs.append({
        "stage": "Stage 2-6 Subject Trajectories & Grid Interpolation",
        "transformation": "Resampled subject curves onto 15-point standard grid using Pchip monotonic interpolation",
        "records_retained": len(df_subj_grid),
        "records_excluded": 0,
        "notes": f"Interpolated {subject_counts} subjects onto T_grid = [0.0 to 24.0 hr]"
    })

    # ----------------------------------------------------
    # STAGE 7: SUBJECT -> DRUG AGGREGATION
    # ----------------------------------------------------
    print("\n[STAGE 7] Aggregating Subject Trajectories to Drug Level...")
    drug_mean_records = []
    stats_records = []
    
    for drug in VALIDATED_DRUGS:
        d_sub = df_subj_grid[df_subj_grid["drug_name"] == drug]
        chembl_id = d_sub["chembl_id"].iloc[0]
        n_subjs = d_sub["subject_id"].nunique()
        
        for t_val in T_GRID:
            t_sub = d_sub[d_sub["time_hr"] == t_val]
            
            c_mean = float(t_sub["concentration"].mean())
            c_med = float(t_sub["concentration"].median())
            c_std = float(t_sub["concentration"].std()) if len(t_sub) > 1 else 0.0
            c_se = float(c_std / np.sqrt(len(t_sub))) if len(t_sub) > 0 else 0.0
            
            cnorm_mean = float(t_sub["dose_norm_conc"].mean())
            cnorm_med = float(t_sub["dose_norm_conc"].median())
            cnorm_std = float(t_sub["dose_norm_conc"].std()) if len(t_sub) > 1 else 0.0
            cnorm_se = float(cnorm_std / np.sqrt(len(t_sub))) if len(t_sub) > 0 else 0.0
            
            cpeak_mean = float(t_sub["peak_norm_conc"].mean())
            cpeak_med = float(t_sub["peak_norm_conc"].median())
            cpeak_std = float(t_sub["peak_norm_conc"].std()) if len(t_sub) > 1 else 0.0
            cpeak_se = float(cpeak_std / np.sqrt(len(t_sub))) if len(t_sub) > 0 else 0.0
            
            drug_mean_records.append({
                "drug_name": drug,
                "chembl_id": chembl_id,
                "time_hr": t_val,
                "mean_concentration": round(c_mean, 6),
                "median_concentration": round(c_med, 6),
                "dose_norm_mean": round(cnorm_mean, 8),
                "peak_norm_mean": round(cpeak_mean, 6),
                "n_subjects": n_subjs
            })
            
            stats_records.append({
                "drug": drug,
                "time": t_val,
                "mean": round(c_mean, 6),
                "median": round(c_med, 6),
                "std": round(c_std, 6),
                "n_subjects": n_subjs,
                "standard_error": round(c_se, 6),
                "dose_norm_mean": round(cnorm_mean, 8),
                "dose_norm_se": round(cnorm_se, 8),
                "peak_norm_mean": round(cpeak_mean, 6),
                "peak_norm_se": round(cpeak_se, 6)
            })

    df_drug_means = pd.DataFrame(drug_mean_records)
    df_drug_means.to_csv(OUT_DRUG_MEAN_TRAJ_CSV, index=False)
    print(f"  Saved drug-level mean trajectories ({len(df_drug_means)} rows) to {OUT_DRUG_MEAN_TRAJ_CSV}")
    
    df_stats = pd.DataFrame(stats_records)
    df_stats.to_csv(OUT_STATISTICS_CSV, index=False)
    print(f"  Saved trajectory statistics table ({len(df_stats)} rows) to {OUT_STATISTICS_CSV}")

    # ----------------------------------------------------
    # STAGE 8: MATRIX VALIDATION & EXPORT
    # ----------------------------------------------------
    print("\n[STAGE 8] Constructing and Validating 7x15 Candidate Matrices...")
    
    df_dose_mat = df_drug_means.pivot(index="drug_name", columns="time_hr", values="dose_norm_mean")
    df_peak_mat = df_drug_means.pivot(index="drug_name", columns="time_hr", values="peak_norm_mean")
    
    df_dose_mat.to_csv(OUT_DOSE_NORM_MATRIX_CSV)
    df_peak_mat.to_csv(OUT_PEAK_NORM_MATRIX_CSV)
    print(f"  Saved 7x15 Dose-Normalized Matrix to {OUT_DOSE_NORM_MATRIX_CSV}")
    print(f"  Saved 7x15 Peak-Normalized Matrix to {OUT_PEAK_NORM_MATRIX_CSV}")
    
    # Assert matrix integrity
    assert df_dose_mat.shape == (7, 15), f"Expected dose matrix shape (7, 15), got {df_dose_mat.shape}"
    assert df_peak_mat.shape == (7, 15), f"Expected peak matrix shape (7, 15), got {df_peak_mat.shape}"
    assert df_dose_mat.isna().sum().sum() == 0, "Dose matrix contains NaN values!"
    assert df_peak_mat.isna().sum().sum() == 0, "Peak matrix contains NaN values!"
    assert not np.isinf(df_dose_mat.values).any(), "Dose matrix contains Inf values!"
    assert not np.isinf(df_peak_mat.values).any(), "Peak matrix contains Inf values!"
    
    audit_logs.append({
        "stage": "Stage 8 Matrix Validation & Export",
        "transformation": "Pivoted drug means to 7x15 dose-normalized and peak-normalized candidate matrices",
        "records_retained": 7,
        "records_excluded": 0,
        "notes": "Verified 7x15 dimensions, 0 NaNs, 0 Infs, 100% finite values"
    })
    
    df_audit = pd.DataFrame(audit_logs)
    df_audit.to_csv(OUT_AUDIT_CSV, index=False)
    print(f"  Saved preprocessing audit log ({len(df_audit)} stages) to {OUT_AUDIT_CSV}")

    print("\nPhase 5A Modeling Matrix Preparation completed successfully.")

if __name__ == "__main__":
    run_phase5a_pipeline()
