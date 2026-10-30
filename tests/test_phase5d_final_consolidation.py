"""
test_phase5d_final_consolidation.py
===================================
Unit tests for Phase 5D final integrated validation and consolidation outputs.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

WORKSPACE_DIR = Path(__file__).parent.parent
FINAL_DATA_DIR = WORKSPACE_DIR / "data" / "processed" / "final"
FINAL_FIGURES_DIR = WORKSPACE_DIR / "outputs" / "figures" / "final"

EXPECTED_DRUGS = [
    "cefamandole",
    "indomethacin",
    "phenobarbital",
    "quinidine",
    "remifentanil",
    "theophylline",
    "xanomeline"
]

def test_phase5d_master_files_exist():
    required_csvs = [
        "final_cohort_summary.csv",
        "final_svd_dmd_results.csv",
        "final_pk_similarity_summary.csv",
        "final_target_network_summary.csv",
        "final_clustering_summary.csv",
        "final_pk_target_coupling_summary.csv",
        "final_integrated_results.csv"
    ]
    for fname in required_csvs:
        fpath = FINAL_DATA_DIR / fname
        assert fpath.exists(), f"Phase 5D master table {fname} is missing!"
        
    assert (FINAL_DATA_DIR / "PHASE_5D_STATUS.md").exists(), "PHASE_5D_STATUS.md missing in data/processed/final/"
    assert (WORKSPACE_DIR / "PHASE_5D_STATUS.md").exists(), "PHASE_5D_STATUS.md missing in workspace root"

def test_phase5d_figures_exist():
    required_figs = [
        "final_svd_variance_spectrum.png",
        "final_standardized_pk_trajectories.png",
        "final_hierarchical_clustering_dendrogram.png",
        "final_svd_clustering_scatter.png",
        "final_pk_vs_target_coupling_scatter.png",
        "final_mantel_permutation_distributions.png",
        "final_integrated_pipeline_overview.png"
    ]
    for fname in required_figs:
        fpath = FINAL_FIGURES_DIR / fname
        assert fpath.exists(), f"Phase 5D final figure {fname} is missing!"

def test_phase5d_cohort_summary():
    df = pd.read_csv(FINAL_DATA_DIR / "final_cohort_summary.csv")
    assert len(df) == 7, f"Expected 7 drugs in cohort summary, got {len(df)}"
    assert list(df["drug_name"]) == EXPECTED_DRUGS, "Cohort summary drug ordering mismatch"
    assert "tetracycline" not in df["drug_name"].values, "Tetracycline found in cohort summary"
    assert df["n_human_subjects"].sum() == 452, f"Expected 452 subjects total, got {df['n_human_subjects'].sum()}"
    assert df["n_valid_pk_observations"].sum() == 5174, f"Expected 5,174 valid obs, got {df['n_valid_pk_observations'].sum()}"
    assert df.isna().sum().sum() == 0, "Cohort summary contains NaNs"

def test_phase5d_svd_results():
    df = pd.read_csv(FINAL_DATA_DIR / "final_svd_dmd_results.csv")
    assert len(df) == 7, f"Expected 7 SVD ranks, got {len(df)}"
    assert df["peak_cumulative_variance_pct"].iloc[1] >= 93.0, "Rank r=2 cumulative variance must be >=93%"
    assert np.isclose(df["peak_cumulative_variance_pct"].iloc[-1], 100.0, atol=0.1), "Cumulative variance must reach 100%"
    assert (np.diff(df["peak_singular_value"]) <= 0).all(), "Singular values not monotonically non-increasing"
    assert df.isna().sum().sum() == 0, "SVD results contain NaNs"

def test_phase5d_target_network_summary():
    df = pd.read_csv(FINAL_DATA_DIR / "final_target_network_summary.csv")
    assert df["total_drugs"].iloc[0] == 7, "Total drugs must be 7"
    assert df["total_unique_target_proteins"].iloc[0] == 196, "Total targets must be 196"
    assert df["total_interaction_edges"].iloc[0] == 222, "Total edges must be 222"

def test_phase5d_coupling_summary():
    df = pd.read_csv(FINAL_DATA_DIR / "final_pk_target_coupling_summary.csv")
    assert len(df) == 6, f"Expected 6 coupling rows, got {len(df)}"
    assert (df["n_pairs"] == 21).all(), "All comparisons must evaluate exactly 21 unique pairs"
    assert (df["n_permutations"] == 10000).all(), "Permutation count must be 10,000"
    for p in df["mantel_p_value"]:
        assert 0.0 <= p <= 1.0, f"Invalid Mantel p-value {p}"

def test_phase5d_integrated_master_table():
    df = pd.read_csv(FINAL_DATA_DIR / "final_integrated_results.csv")
    assert len(df) >= 7, "Integrated results table must contain all pipeline stages"
    assert (df["scientific_status"].isin(["VALIDATED", "EXPLORATORY_NON_SIGNIFICANT"])).all()
