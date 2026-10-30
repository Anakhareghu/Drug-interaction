"""
test_phase4b_ingestion.py
==========================
Unit tests for Phase 4B replacement PK dataset ingestion & validation.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

WORKSPACE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = WORKSPACE_DIR / "data" / "processed"
CLEAN_CSV = PROCESSED_DIR / "pk_phase4_clean.csv"
AUDIT_CSV = PROCESSED_DIR / "pk_phase4_ingestion_audit.csv"

def test_phase4_clean_file_exists():
    assert CLEAN_CSV.exists(), "pk_phase4_clean.csv does not exist"

def test_phase4_audit_file_exists():
    assert AUDIT_CSV.exists(), "pk_phase4_ingestion_audit.csv does not exist"

def test_phase4_clean_schema_and_contents():
    df = pd.read_csv(CLEAN_CSV)
    required_cols = [
        "drug_name", "chembl_id", "study_id", "subject_id",
        "time_hr", "concentration", "concentration_unit",
        "biological_matrix", "route", "dose_mg", "is_plasma_concentration"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column {col} in pk_phase4_clean.csv"

    assert len(df) > 2000, f"Expected >2000 observations, got {len(df)}"
    assert df["is_plasma_concentration"].all(), "All records must have is_plasma_concentration == True"
    assert df["concentration"].min() > 0, "All concentration values must be positive"
    assert df["time_hr"].min() >= 0, "Time values must be non-negative"
    assert set(df["biological_matrix"].unique()).issubset({"plasma", "serum"}), "Matrix must be plasma or serum"

def test_phase4_chembl_linkage():
    df = pd.read_csv(CLEAN_CSV)
    drugs = df["drug_name"].unique()
    assert len(drugs) == 6, f"Expected 6 drugs, got {len(drugs)}"
    for drug in drugs:
        chembl_id = df[df["drug_name"] == drug]["chembl_id"].iloc[0]
        assert str(chembl_id).startswith("CHEMBL"), f"Invalid ChEMBL ID {chembl_id} for drug {drug}"
