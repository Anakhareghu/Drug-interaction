"""
test_phase5c3_clustering_coupling.py
====================================
Unit tests for Phase 5C.3 PK trajectory clustering and PK-target analytical coupling.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

WORKSPACE_DIR = Path(__file__).parent.parent
PHASE5C_DIR = WORKSPACE_DIR / "data" / "processed" / "phase5c"
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

def test_phase5c3_output_files_exist():
    required_files = [
        "clustering_assignments.csv",
        "clustering_metrics.csv",
        "pk_target_pairwise_comparisons.csv",
        "pk_target_coupling_results.csv",
        "PHASE_5C_3_STATUS.md"
    ]
    for fname in required_files:
        fpath = PHASE5C_DIR / fname
        assert fpath.exists(), f"Phase 5C.3 output file {fname} is missing!"

def test_phase5c3_figures_exist():
    required_figures = [
        "pk_hierarchical_dendrograms.png",
        "pk_svd_clusters_scatter.png",
        "pk_vs_target_distance_scatter.png",
        "mantel_permutation_distributions.png",
        "pk_target_coupling_summary.png"
    ]
    for fname in required_figures:
        fpath = FIGURES_DIR / fname
        assert fpath.exists(), f"Phase 5C.3 figure {fname} is missing!"

def test_phase5c3_clustering_assignments():
    df = pd.read_csv(PHASE5C_DIR / "clustering_assignments.csv")
    assert len(df) == 7, f"Expected 7 drugs in clustering assignments, got {len(df)}"
    assert list(df["drug_name"]) == EXPECTED_DRUGS, "Clustering assignments drug ordering mismatch"
    assert "tetracycline" not in df["drug_name"].values, "Rejected drug tetracycline found"
    
    for col in ["svd_ward_k2", "svd_avg_k2", "dtw_avg_k2", "kmeans_k2"]:
        assert set(df[col].unique()).issubset({1, 2}), f"k=2 labels out of range in {col}"
        
    for col in ["svd_ward_k3", "svd_avg_k3", "dtw_avg_k3", "kmeans_k3"]:
        assert set(df[col].unique()).issubset({1, 2, 3}), f"k=3 labels out of range in {col}"
        
    assert df.isna().sum().sum() == 0, "Clustering assignments contain NaNs"

def test_phase5c3_pairwise_comparisons():
    df = pd.read_csv(PHASE5C_DIR / "pk_target_pairwise_comparisons.csv")
    assert len(df) == 21, f"Expected exactly 21 unique pairwise comparisons (7*6/2), got {len(df)}"
    
    required_cols = [
        "pair_index", "drug_1", "drug_2",
        "d_pk_svd_peak", "d_pk_svd_dose", "d_pk_dtw_peak",
        "s_target_jaccard", "s_target_cosine",
        "d_target_jaccard", "d_target_cosine"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column {col} in pairwise comparisons"
        
    # Verify non-negativity
    assert (df["d_pk_svd_peak"] >= 0).all()
    assert (df["d_pk_dtw_peak"] >= 0).all()
    assert (df["d_target_jaccard"] >= 0).all()
    assert (df["d_target_cosine"] >= 0).all()
    assert (df["s_target_jaccard"] >= 0).all() and (df["s_target_jaccard"] <= 1.0).all()
    assert df.isna().sum().sum() == 0, "Pairwise comparisons contain NaNs"

def test_phase5c3_coupling_results():
    df = pd.read_csv(PHASE5C_DIR / "pk_target_coupling_results.csv")
    assert len(df) >= 4, f"Expected at least 4 coupling comparisons, got {len(df)}"
    
    for _, row in df.iterrows():
        assert -1.0 <= row["spearman_rho"] <= 1.0, f"Spearman rho out of range: {row['spearman_rho']}"
        assert -1.0 <= row["pearson_r"] <= 1.0, f"Pearson r out of range: {row['pearson_r']}"
        assert 0.0 <= row["mantel_p_value"] <= 1.0, f"Mantel p-value out of range: {row['mantel_p_value']}"
        assert row["n_permutations"] == 10000, f"Expected 10,000 permutations, got {row['n_permutations']}"
        assert row["n_pairs"] == 21, f"Expected 21 pairs, got {row['n_pairs']}"
        
    assert df.isna().sum().sum() == 0, "Coupling results contain NaNs"
