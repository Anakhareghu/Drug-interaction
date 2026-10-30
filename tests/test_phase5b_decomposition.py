"""
test_phase5b_decomposition.py
==============================
Unit tests for Phase 5B SVD and Dynamic Mode Decomposition (DMD).
"""

import pytest
import pandas as pd
import numpy as np
import scipy.linalg as la
from pathlib import Path

WORKSPACE_DIR = Path(__file__).parent.parent
PROCESSED_PHASE5B_DIR = WORKSPACE_DIR / "data" / "processed" / "phase5b"
FIGURES_DIR = WORKSPACE_DIR / "outputs" / "figures" / "phase5b"

EXPECTED_DRUGS = ["cefamandole", "indomethacin", "phenobarbital", "quinidine", "remifentanil", "theophylline", "xanomeline"]

def test_phase5b_csv_outputs_exist():
    required_files = [
        "svd_singular_values.csv",
        "svd_explained_variance.csv",
        "svd_u_matrix_dose.csv",
        "svd_u_matrix_peak.csv",
        "svd_vt_matrix_dose.csv",
        "svd_vt_matrix_peak.csv",
        "svd_scores_dose.csv",
        "svd_scores_peak.csv",
        "svd_reconstruction_errors.csv",
        "dmd_eigenvalues.csv",
        "dmd_reconstructions_dose.csv",
        "dmd_reconstructions_peak.csv",
        "phase5b_validation_summary.csv"
    ]
    for fname in required_files:
        fpath = PROCESSED_PHASE5B_DIR / fname
        assert fpath.exists(), f"Phase 5B output CSV {fname} is missing!"

def test_phase5b_figures_exist():
    required_figures = [
        "svd_singular_values.png",
        "svd_explained_variance.png",
        "svd_temporal_modes.png",
        "svd_drug_loadings.png",
        "dmd_eigenvalues.png",
        "svd_dmd_reconstructions.png",
        "svd_reconstruction_errors.png"
    ]
    for fname in required_figures:
        fpath = FIGURES_DIR / fname
        assert fpath.exists(), f"Phase 5B figure {fname} is missing!"

def test_phase5b_svd_reconstruction_identity():
    # Test mathematical exactness X = U * S * Vt
    dose_mat = pd.read_csv(WORKSPACE_DIR / "data" / "processed" / "pk_phase5_dose_normalized_matrix.csv", index_col=0).values
    peak_mat = pd.read_csv(WORKSPACE_DIR / "data" / "processed" / "pk_phase5_peak_normalized_matrix.csv", index_col=0).values

    for norm_name, X in [("dose", dose_mat), ("peak", peak_mat)]:
        df_u = pd.read_csv(PROCESSED_PHASE5B_DIR / f"svd_u_matrix_{norm_name}.csv", index_col=0).values
        df_vt = pd.read_csv(PROCESSED_PHASE5B_DIR / f"svd_vt_matrix_{norm_name}.csv", index_col=0).values
        df_s = pd.read_csv(PROCESSED_PHASE5B_DIR / "svd_singular_values.csv")[f"{norm_name}_singular_value"].values
        
        X_reconstructed = df_u @ np.diag(df_s) @ df_vt
        diff = np.abs(X - X_reconstructed).max()
        assert diff < 1e-10, f"SVD reconstruction error exceeds tolerance for {norm_name} (diff={diff})"

def test_phase5b_singular_values_and_explained_variance():
    df_s = pd.read_csv(PROCESSED_PHASE5B_DIR / "svd_singular_values.csv")
    df_var = pd.read_csv(PROCESSED_PHASE5B_DIR / "svd_explained_variance.csv")

    for col in ["dose_singular_value", "peak_singular_value"]:
        s = df_s[col].values
        assert (np.diff(s) <= 0).all(), f"Singular values in {col} are not monotonically non-increasing!"

    for col in ["dose_exp_var_ratio", "peak_exp_var_ratio"]:
        var_sum = df_var[col].sum()
        assert np.isclose(var_sum, 1.0, atol=1e-5), f"Explained variance ratios in {col} do not sum to 1.0 (sum={var_sum})"

def test_phase5b_dmd_properties():
    df_dmd_evals = pd.read_csv(PROCESSED_PHASE5B_DIR / "dmd_eigenvalues.csv")
    assert len(df_dmd_evals) == 6, f"Expected 6 eigenvalues (3 for dose, 3 for peak), got {len(df_dmd_evals)}"
    assert df_dmd_evals["magnitude"].min() > 0, "DMD eigenvalue magnitudes must be positive"
    assert df_dmd_evals["real_part"].isna().sum() == 0, "DMD real parts contain NaNs"
