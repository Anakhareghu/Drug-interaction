"""
test_phase5c1_similarity.py
===========================
Unit tests for Phase 5C.1 PK trajectory similarity and distance matrices.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

WORKSPACE_DIR = Path(__file__).parent.parent
PHASE5C_DATA_DIR = WORKSPACE_DIR / "data" / "processed" / "phase5c"
FIGURES_DIR = WORKSPACE_DIR / "outputs" / "figures" / "phase5c"

EXPECTED_DRUGS = [
    "cefamandole",
    "indomethacin",
    "phenobarbital",
    "quinidine",
    "remifentanil",
    "theophylline",
    "xanomeline"
]

def test_phase5c1_csv_outputs_exist():
    required_files = [
        "pk_svd_distance_peak.csv",
        "pk_svd_distance_dose.csv",
        "pk_dtw_distance_peak.csv",
        "PHASE_5C_1_STATUS.md"
    ]
    for fname in required_files:
        fpath = PHASE5C_DATA_DIR / fname
        assert fpath.exists(), f"Phase 5C.1 output file {fname} is missing!"

def test_phase5c1_figures_exist():
    required_figures = [
        "pk_svd_distance_peak_heatmap.png",
        "pk_svd_distance_dose_heatmap.png",
        "pk_dtw_distance_peak_heatmap.png",
        "pk_distance_comparison_heatmap.png"
    ]
    for fname in required_figures:
        fpath = FIGURES_DIR / fname
        assert fpath.exists(), f"Phase 5C.1 figure {fname} is missing!"

def test_phase5c1_matrix_dimensions_and_cohort():
    for fname in ["pk_svd_distance_peak.csv", "pk_svd_distance_dose.csv", "pk_dtw_distance_peak.csv"]:
        df = pd.read_csv(PHASE5C_DATA_DIR / fname, index_col=0)
        assert df.shape == (7, 7), f"{fname} must be a 7x7 matrix, got {df.shape}"
        assert list(df.index) == EXPECTED_DRUGS, f"{fname} row index does not match canonical 7 drugs"
        assert list(df.columns) == EXPECTED_DRUGS, f"{fname} column names do not match canonical 7 drugs"
        assert "tetracycline" not in df.index, f"Rejected drug tetracycline found in {fname}"
        assert df.isna().sum().sum() == 0, f"{fname} contains NaN values"
        assert not np.isinf(df.values).any(), f"{fname} contains Infinite values"

def test_phase5c1_matrix_symmetry_and_diagonal():
    for fname in ["pk_svd_distance_peak.csv", "pk_svd_distance_dose.csv", "pk_dtw_distance_peak.csv"]:
        df = pd.read_csv(PHASE5C_DATA_DIR / fname, index_col=0)
        D = df.values
        
        # Test exact symmetry D = D.T
        assert np.allclose(D, D.T, atol=1e-12), f"{fname} is not symmetric!"
        
        # Test zero diagonal D_ii = 0
        assert np.allclose(np.diag(D), 0.0, atol=1e-12), f"{fname} diagonal is non-zero!"
        
        # Test non-negative distances D_ij >= 0
        assert (D >= 0).all(), f"{fname} contains negative distance values!"
        
        # Test that off-diagonal entries are strictly positive (distinct drugs)
        off_diag = D[~np.eye(7, dtype=bool)]
        assert (off_diag > 0).all(), f"{fname} contains zero off-diagonal distance between distinct drugs!"

def test_phase5c1_svd_triangle_inequality():
    # Euclidean distance metric must satisfy triangle inequality: d(i, k) <= d(i, j) + d(j, k)
    for fname in ["pk_svd_distance_peak.csv", "pk_svd_distance_dose.csv"]:
        df = pd.read_csv(PHASE5C_DATA_DIR / fname, index_col=0)
        D = df.values
        n = len(D)
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    assert D[i, k] <= D[i, j] + D[j, k] + 1e-10, f"Triangle inequality violated in {fname} for ({i},{j},{k})"
