"""
test_phase5c2_chembl_network.py
================================
Unit tests for Phase 5C.2 ChEMBL Drug-Target Network & Similarity Matrices.
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

def test_phase5c2_output_files_exist():
    required_files = [
        "chembl_target_bipartite_matrix.csv",
        "chembl_drug_target_edges.csv",
        "chembl_target_jaccard_similarity.csv",
        "chembl_target_cosine_similarity.csv",
        "PHASE_5C_2_STATUS.md"
    ]
    for fname in required_files:
        fpath = PHASE5C_DIR / fname
        assert fpath.exists(), f"Phase 5C.2 output file {fname} is missing!"

def test_phase5c2_figures_exist():
    required_figures = [
        "bipartite_drug_target_network.png",
        "chembl_target_jaccard_heatmap.png",
        "chembl_target_cosine_heatmap.png",
        "chembl_target_comparison_heatmap.png"
    ]
    for fname in required_figures:
        fpath = FIGURES_DIR / fname
        assert fpath.exists(), f"Phase 5C.2 figure {fname} is missing!"

def test_phase5c2_bipartite_matrix_schema_and_integrity():
    bipartite_csv = PHASE5C_DIR / "chembl_target_bipartite_matrix.csv"
    df_bip = pd.read_csv(bipartite_csv, index_col=0)
    
    # 7 drugs as rows
    assert df_bip.shape[0] == 7, f"Expected 7 rows, got {df_bip.shape[0]}"
    assert list(df_bip.index) == EXPECTED_DRUGS, "Row index does not match canonical 7 drugs"
    assert "tetracycline" not in df_bip.index, "Rejected drug tetracycline found in bipartite matrix"
    
    # At least 1 target
    assert df_bip.shape[1] > 0, "Bipartite matrix has 0 target columns"
    
    # All values must be binary 0 or 1
    unique_vals = set(np.unique(df_bip.values))
    assert unique_vals.issubset({0, 1}), f"Bipartite matrix contains non-binary values: {unique_vals}"
    assert df_bip.isna().sum().sum() == 0, "Bipartite matrix contains NaNs"

def test_phase5c2_edge_list_consistency():
    edges_csv = PHASE5C_DIR / "chembl_drug_target_edges.csv"
    bipartite_csv = PHASE5C_DIR / "chembl_target_bipartite_matrix.csv"
    
    df_edges = pd.read_csv(edges_csv)
    df_bip = pd.read_csv(bipartite_csv, index_col=0)
    
    # Check required columns
    required_cols = [
        "drug_name", "molecule_chembl_id", "target_chembl_id",
        "target_name", "target_type", "organism", "uniprot_accession",
        "evidence_type"
    ]
    for col in required_cols:
        assert col in df_edges.columns, f"Missing required column {col} in edge list"
        
    assert set(df_edges["drug_name"].unique()).issubset(set(EXPECTED_DRUGS))
    assert "tetracycline" not in df_edges["drug_name"].values
    
    # Edge count in edge list must match number of 1s in bipartite matrix
    total_bip_ones = int(df_bip.values.sum())
    assert len(df_edges) == total_bip_ones, f"Edge list count ({len(df_edges)}) != bipartite matrix 1s ({total_bip_ones})"

def test_phase5c2_similarity_matrices_properties():
    for fname in ["chembl_target_jaccard_similarity.csv", "chembl_target_cosine_similarity.csv"]:
        df_sim = pd.read_csv(PHASE5C_DIR / fname, index_col=0)
        
        # Dimensions
        assert df_sim.shape == (7, 7), f"{fname} must be 7x7, got {df_sim.shape}"
        assert list(df_sim.index) == EXPECTED_DRUGS, f"{fname} index mismatch"
        assert list(df_sim.columns) == EXPECTED_DRUGS, f"{fname} columns mismatch"
        
        S = df_sim.values
        
        # Symmetry S = S.T
        assert np.allclose(S, S.T, atol=1e-12), f"{fname} is not symmetric"
        
        # Diagonal == 1.0
        assert np.allclose(np.diag(S), 1.0, atol=1e-12), f"{fname} diagonal is not 1.0"
        
        # Values bounded in [0.0, 1.0]
        assert (S >= -1e-10).all() and (S <= 1.0 + 1e-10).all(), f"{fname} values out of bounds [0, 1]"
        assert df_sim.isna().sum().sum() == 0, f"{fname} contains NaNs"
