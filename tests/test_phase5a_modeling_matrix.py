"""
test_phase5a_modeling_matrix.py
=================================
Unit tests for Phase 5A modeling matrix preparation and preprocessing.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

WORKSPACE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = WORKSPACE_DIR / "data" / "processed"

SUBJECT_TRAJ_CSV = PROCESSED_DIR / "pk_phase5_subject_trajectories.csv"
DRUG_MEAN_TRAJ_CSV = PROCESSED_DIR / "pk_phase5_drug_mean_trajectories.csv"
DOSE_NORM_MATRIX_CSV = PROCESSED_DIR / "pk_phase5_dose_normalized_matrix.csv"
PEAK_NORM_MATRIX_CSV = PROCESSED_DIR / "pk_phase5_peak_normalized_matrix.csv"
STATISTICS_CSV = PROCESSED_DIR / "pk_phase5_trajectory_statistics.csv"
AUDIT_CSV = PROCESSED_DIR / "pk_phase5_preprocessing_audit.csv"

EXPECTED_DRUGS = ["cefamandole", "indomethacin", "phenobarbital", "quinidine", "remifentanil", "theophylline", "xanomeline"]
EXPECTED_GRID = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0, 24.0]

def test_phase5a_output_files_exist():
    assert SUBJECT_TRAJ_CSV.exists(), "pk_phase5_subject_trajectories.csv missing"
    assert DRUG_MEAN_TRAJ_CSV.exists(), "pk_phase5_drug_mean_trajectories.csv missing"
    assert DOSE_NORM_MATRIX_CSV.exists(), "pk_phase5_dose_normalized_matrix.csv missing"
    assert PEAK_NORM_MATRIX_CSV.exists(), "pk_phase5_peak_normalized_matrix.csv missing"
    assert STATISTICS_CSV.exists(), "pk_phase5_trajectory_statistics.csv missing"
    assert AUDIT_CSV.exists(), "pk_phase5_preprocessing_audit.csv missing"

def test_phase5a_subject_trajectories_schema_and_values():
    df = pd.read_csv(SUBJECT_TRAJ_CSV)
    required_cols = [
        "drug_name", "chembl_id", "study_id", "subject_id",
        "time_hr", "concentration", "dose_norm_conc", "peak_norm_conc",
        "dose_mg", "cmax_subject", "biological_matrix", "route"
    ]
    for col in required_cols:
        assert col in df.columns, f"Column {col} missing from subject trajectories"

    assert len(df) == 452 * 15, f"Expected 452 subjects x 15 grid points = 6780, got {len(df)}"
    assert df["concentration"].min() >= 0, "Concentrations must be non-negative"
    assert df["dose_norm_conc"].min() >= 0, "Dose-normalized concentrations must be non-negative"
    assert df["peak_norm_conc"].min() >= 0, "Peak-normalized concentrations must be non-negative"
    assert df["peak_norm_conc"].max() <= 1.000001, "Peak-normalized concentrations cannot exceed 1.0"
    assert set(df["drug_name"].unique()) == set(EXPECTED_DRUGS), "Unexpected set of drugs"

def test_phase5a_dose_and_peak_normalized_matrices():
    df_dose = pd.read_csv(DOSE_NORM_MATRIX_CSV, index_col="drug_name")
    df_peak = pd.read_csv(PEAK_NORM_MATRIX_CSV, index_col="drug_name")

    # Verify dimensions (7 drugs x 15 timepoints)
    assert df_dose.shape == (7, 15), f"Expected dose matrix shape (7, 15), got {df_dose.shape}"
    assert df_peak.shape == (7, 15), f"Expected peak matrix shape (7, 15), got {df_peak.shape}"

    # Verify rows & columns
    assert list(df_dose.index) == EXPECTED_DRUGS, "Dose matrix drug index mismatch"
    assert list(df_peak.index) == EXPECTED_DRUGS, "Peak matrix drug index mismatch"
    
    # Verify no NaNs or Infs
    assert df_dose.isna().sum().sum() == 0, "Dose matrix contains NaNs"
    assert df_peak.isna().sum().sum() == 0, "Peak matrix contains NaNs"
    assert not np.isinf(df_dose.values).any(), "Dose matrix contains Infs"
    assert not np.isinf(df_peak.values).any(), "Peak matrix contains Infs"

    # Peak matrix max <= 1.0
    assert df_peak.values.max() <= 1.000001, "Peak matrix values cannot exceed 1.0"
    assert df_peak.values.min() >= 0.0, "Peak matrix values cannot be negative"

def test_phase5a_statistics_and_audit():
    df_stats = pd.read_csv(STATISTICS_CSV)
    assert len(df_stats) == 7 * 15, f"Expected 105 rows of stats, got {len(df_stats)}"
    for col in ["mean", "median", "std", "n_subjects", "standard_error"]:
        assert col in df_stats.columns, f"Missing stat column {col}"
        
    df_audit = pd.read_csv(AUDIT_CSV)
    assert len(df_audit) >= 3, "Audit table must record all pipeline stages"
