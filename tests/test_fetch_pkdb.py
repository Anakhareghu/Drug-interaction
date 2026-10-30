"""
tests/test_fetch_pkdb.py
========================
Unit tests for Phase 1 PK-DB data fetcher.
Tests API response parsing, pagination helpers, and data integrity.
"""

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from fetch_pkdb import (
    _paginate,
    fetch_substances,
    fetch_timecourses,
    fetch_interventions,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_SUBSTANCE = {
    "sid": "caffeine",
    "name": "caffeine",
    "label": "caffeine (137X)",
    "ntype": "substance",
    "dtype": "undefined",
    "description": "A methylxanthine alkaloid.",
    "synonyms": ["Caffeine", "1,3,7-trimethylxanthine"],
    "parents": [],
    "annotations": [
        {
            "label": None,
            "relation": "BQB_IS",
            "term": "RYYVLZVUVIJVGH-UHFFFAOYSA-N",
            "collection": "inchikey",
            "description": None,
        }
    ],
    "xrefs": [
        {
            "name": "chembl",
            "accession": "CHEMBL113",
            "url": "https://www.ebi.ac.uk/chembldb/compound/inspect/CHEMBL113",
        },
        {
            "name": "pubchem",
            "accession": "2519",
            "url": "http://pubchem.ncbi.nlm.nih.gov/compound/2519",
        },
    ],
    "substance": {"mass": 194.1906, "charge": 0.0, "formula": "C8H10N4O2"},
}

MOCK_SINGLE_PAGE_RESPONSE = {
    "current_page": 1,
    "last_page": 1,
    "next_page_url": None,
    "prev_page_url": None,
    "data": {
        "count": 1,
        "data": [MOCK_SUBSTANCE],
    },
}


# ---------------------------------------------------------------------------
# _paginate tests
# ---------------------------------------------------------------------------

class TestPaginate:
    @patch("fetch_pkdb.requests.Session")
    def test_single_page(self, mock_session_cls):
        """Should return all records from a single-page response."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SINGLE_PAGE_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        records = _paginate("info_nodes", extra_params={"ntype": "substance"})
        assert len(records) == 1
        assert records[0]["sid"] == "caffeine"

    @patch("fetch_pkdb.requests.Session")
    @patch("fetch_pkdb.time.sleep")  # suppress real sleep
    def test_multipage_collects_all(self, mock_sleep, mock_session_cls):
        """Should concatenate records across multiple pages."""
        page1 = {
            "current_page": 1,
            "last_page": 2,
            "data": {"count": 2, "data": [{"sid": "caffeine"}]},
        }
        page2 = {
            "current_page": 2,
            "last_page": 2,
            "data": {"count": 2, "data": [{"sid": "midazolam"}]},
        }

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.side_effect = [page1, page2]
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        records = _paginate("info_nodes")
        assert len(records) == 2
        assert {r["sid"] for r in records} == {"caffeine", "midazolam"}

    @patch("fetch_pkdb.requests.Session")
    @patch("fetch_pkdb.time.sleep")
    def test_max_pages_respected(self, mock_sleep, mock_session_cls):
        """max_pages should limit the number of pages fetched."""
        # 5 pages exist but we only want 2
        def make_page(n, last=5):
            return {
                "current_page": n,
                "last_page": last,
                "data": {"count": last, "data": [{"sid": f"drug_{n}"}]},
            }

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.side_effect = [make_page(1), make_page(2)]
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        records = _paginate("info_nodes", max_pages=2)
        assert len(records) == 2

    @patch("fetch_pkdb.requests.Session")
    def test_empty_data(self, mock_session_cls):
        """Should gracefully handle empty data arrays."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "current_page": 1,
            "last_page": 1,
            "data": {"count": 0, "data": []},
        }
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        records = _paginate("pkdata/timecourses")
        assert records == []


# ---------------------------------------------------------------------------
# fetch_substances tests
# ---------------------------------------------------------------------------

class TestFetchSubstances:
    @patch("fetch_pkdb._paginate")
    def test_saves_json(self, mock_paginate, tmp_path):
        """Saved JSON should include metadata and data array."""
        mock_paginate.return_value = [MOCK_SUBSTANCE]
        out_dir = tmp_path / "pkdb"

        substances = fetch_substances(out_dir)

        assert (out_dir / "substances.json").exists()
        assert len(substances) == 1

        payload = json.loads((out_dir / "substances.json").read_text())
        assert "source" in payload
        assert "endpoint" in payload
        assert "count" in payload
        assert payload["count"] == 1
        assert "data" in payload
        assert payload["data"][0]["sid"] == "caffeine"

    @patch("fetch_pkdb._paginate")
    def test_returns_substances_list(self, mock_paginate, tmp_path):
        """fetch_substances should return the list of substance records."""
        mock_paginate.return_value = [MOCK_SUBSTANCE, {"sid": "morphine"}]
        out_dir = tmp_path / "pkdb"
        substances = fetch_substances(out_dir)
        assert len(substances) == 2


# ---------------------------------------------------------------------------
# Data integrity tests
# ---------------------------------------------------------------------------

class TestSubstanceSchema:
    """Validate that MOCK_SUBSTANCE has the expected schema."""

    def test_has_required_fields(self):
        required = ["sid", "name", "label", "ntype", "xrefs", "annotations"]
        for field in required:
            assert field in MOCK_SUBSTANCE, f"Field '{field}' missing"

    def test_chembl_xref_format(self):
        chembl_xrefs = [
            x for x in MOCK_SUBSTANCE["xrefs"] if x.get("name") == "chembl"
        ]
        assert len(chembl_xrefs) == 1
        acc = chembl_xrefs[0]["accession"]
        assert acc.startswith("CHEMBL"), f"Bad ChEMBL accession: {acc}"
        assert acc[len("CHEMBL"):].isdigit(), f"ChEMBL ID not numeric: {acc}"

    def test_inchikey_annotation(self):
        inchikey_anns = [
            a for a in MOCK_SUBSTANCE["annotations"]
            if a.get("collection") == "inchikey"
        ]
        assert len(inchikey_anns) == 1
        key = inchikey_anns[0]["term"]
        # InChIKey format: 14-10-1 characters separated by dashes
        parts = key.split("-")
        assert len(parts) == 3, f"Invalid InChIKey format: {key}"


# ---------------------------------------------------------------------------
# Integration-style test (requires network; skip if offline)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_pkdb_api_reachable():
    """Check that the PK-DB API is reachable (requires network)."""
    import requests

    try:
        resp = requests.get("https://pk-db.com/api/v1/", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert "studies" in data
        assert "info_nodes" in data
    except requests.ConnectionError:
        pytest.skip("PK-DB API not reachable (offline)")
