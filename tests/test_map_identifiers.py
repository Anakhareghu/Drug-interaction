"""
tests/test_map_identifiers.py
==============================
Unit tests for Phase 1 identifier mapping module.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from map_identifiers import (
    build_id_mapping,
    extract_annotation,
    extract_xref,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SUBSTANCE_WITH_CHEMBL = {
    "sid": "midazolam",
    "name": "midazolam",
    "label": "midazolam",
    "ntype": "substance",
    "xrefs": [
        {"name": "chembl", "accession": "CHEMBL665", "url": "..."},
        {"name": "pubchem", "accession": "4192", "url": "..."},
        {"name": "chebi", "accession": "6931", "url": "..."},
    ],
    "annotations": [
        {
            "term": "DDGESRKBKYOEKM-JTQLQIEISA-N",
            "collection": "inchikey",
            "label": None,
        }
    ],
    "substance": {"mass": 325.775, "charge": 0.0, "formula": "C18H13ClFN3O"},
}

SUBSTANCE_NO_CHEMBL_WITH_INCHIKEY = {
    "sid": "some_drug",
    "name": "some drug",
    "label": "some drug",
    "ntype": "substance",
    "xrefs": [
        {"name": "pubchem", "accession": "99999", "url": "..."},
    ],
    "annotations": [
        {
            "term": "ABCDEFGHIJKLMN-ABCDEFGHI-Z",
            "collection": "inchikey",
            "label": None,
        }
    ],
    "substance": {"mass": 200.0, "charge": 0.0, "formula": "C10H10N2O"},
}

SUBSTANCE_NO_IDS = {
    "sid": "abstract_node",
    "name": "abstract",
    "label": "abstract",
    "ntype": "substance",
    "xrefs": [],
    "annotations": [],
    "substance": {"mass": None, "charge": None, "formula": None},
}

SUBSTANCE_WITH_CHEBI_ONLY = {
    "sid": "phenobarbitol",
    "name": "phenobarbitol",
    "label": "phenobarbitol",
    "ntype": "substance",
    "xrefs": [
        {"name": "chebi", "accession": "8069", "url": "..."},
    ],
    "annotations": [],
    "substance": {"mass": 232.2, "charge": 0.0, "formula": "C12H12N2O3"},
}


# ---------------------------------------------------------------------------
# extract_xref tests
# ---------------------------------------------------------------------------

class TestExtractXref:
    def test_chembl_xref_found(self):
        acc = extract_xref(SUBSTANCE_WITH_CHEMBL, "chembl")
        assert acc == "CHEMBL665"

    def test_pubchem_xref_found(self):
        acc = extract_xref(SUBSTANCE_WITH_CHEMBL, "pubchem")
        assert acc == "4192"

    def test_missing_xref_returns_none(self):
        acc = extract_xref(SUBSTANCE_WITH_CHEMBL, "drugbank")
        assert acc is None

    def test_empty_xrefs_returns_none(self):
        acc = extract_xref(SUBSTANCE_NO_IDS, "chembl")
        assert acc is None

    def test_case_insensitive(self):
        acc = extract_xref(SUBSTANCE_WITH_CHEMBL, "CHEMBL")
        assert acc == "CHEMBL665"


# ---------------------------------------------------------------------------
# extract_annotation tests
# ---------------------------------------------------------------------------

class TestExtractAnnotation:
    def test_inchikey_found(self):
        key = extract_annotation(SUBSTANCE_WITH_CHEMBL, "inchikey")
        assert key == "DDGESRKBKYOEKM-JTQLQIEISA-N"

    def test_missing_collection_returns_none(self):
        ann = extract_annotation(SUBSTANCE_WITH_CHEMBL, "chebi")
        assert ann is None  # chebi is in xrefs, not annotations here

    def test_empty_annotations(self):
        ann = extract_annotation(SUBSTANCE_NO_IDS, "inchikey")
        assert ann is None


# ---------------------------------------------------------------------------
# build_id_mapping tests
# ---------------------------------------------------------------------------

class TestBuildIdMapping:
    def test_direct_xref_mapping(self):
        """Substances with direct ChEMBL xref should be mapped via direct_xref."""
        substances = [SUBSTANCE_WITH_CHEMBL]
        df = build_id_mapping(substances, use_api_fallback=False)

        assert len(df) == 1
        row = df.iloc[0]
        assert row["pkdb_sid"] == "midazolam"
        assert row["chembl_id"] == "CHEMBL665"
        assert row["mapping_method"] == "direct_xref"
        assert row["confidence"] == "high"

    def test_no_chembl_without_fallback(self):
        """Without API fallback, substances with no ChEMBL xref should be unmapped."""
        substances = [SUBSTANCE_NO_CHEMBL_WITH_INCHIKEY]
        df = build_id_mapping(substances, use_api_fallback=False)

        assert len(df) == 1
        row = df.iloc[0]
        assert row["chembl_id"] is None or pd.isna(row["chembl_id"])
        assert row["mapping_method"] == "unmapped"

    def test_output_columns(self):
        """DataFrame should have all expected columns."""
        df = build_id_mapping([SUBSTANCE_WITH_CHEMBL], use_api_fallback=False)
        expected_cols = [
            "pkdb_sid", "pkdb_label", "chembl_id",
            "mapping_method", "confidence",
            "inchikey", "chebi_id", "pubchem_id",
        ]
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_multiple_substances(self):
        """Should process multiple substances and return one row each."""
        substances = [
            SUBSTANCE_WITH_CHEMBL,
            SUBSTANCE_NO_CHEMBL_WITH_INCHIKEY,
            SUBSTANCE_NO_IDS,
        ]
        df = build_id_mapping(substances, use_api_fallback=False)
        assert len(df) == 3

    def test_chembl_id_prefix_normalised(self):
        """ChEMBL IDs should be upper-cased and start with 'CHEMBL'."""
        # Lower-case accession in xref
        substance = {
            **SUBSTANCE_WITH_CHEMBL,
            "xrefs": [{"name": "chembl", "accession": "chembl665"}],
        }
        df = build_id_mapping([substance], use_api_fallback=False)
        assert df.iloc[0]["chembl_id"] == "CHEMBL665"

    def test_inchikey_preserved(self):
        """InChIKey should be extracted and stored."""
        df = build_id_mapping([SUBSTANCE_WITH_CHEMBL], use_api_fallback=False)
        assert df.iloc[0]["inchikey"] == "DDGESRKBKYOEKM-JTQLQIEISA-N"

    def test_chebi_from_xref_stored(self):
        """CHEBI accession should be extracted from xrefs if not in annotations."""
        df = build_id_mapping([SUBSTANCE_WITH_CHEBI_ONLY], use_api_fallback=False)
        assert df.iloc[0]["chebi_id"] == "8069"

    def test_empty_substances_list(self):
        """Empty input should return empty DataFrame."""
        df = build_id_mapping([], use_api_fallback=False)
        assert len(df) == 0


# ---------------------------------------------------------------------------
# Integration tests (require network + chembl_webresource_client)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_inchikey_lookup_caffeine():
    """InChIKey for caffeine should resolve to CHEMBL113."""
    try:
        from chembl_webresource_client.new_client import new_client

        nc = new_client
        from map_identifiers import lookup_by_inchikey

        chembl_id = lookup_by_inchikey("RYYVLZVUVIJVGH-UHFFFAOYSA-N", nc)
        assert chembl_id is not None
        assert chembl_id.startswith("CHEMBL")
    except ImportError:
        pytest.skip("chembl_webresource_client not installed")
