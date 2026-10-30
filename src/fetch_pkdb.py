"""
fetch_pkdb.py
=============
Phase 1 — PK-DB Data Collection

Downloads and preserves raw data from the PK-DB REST API:
  - Substance info_nodes (with cross-references including ChEMBL IDs)
  - Study metadata (pkdata/studies) with licence/access information
  - Concentration time-series for open-licence studies (via TSV media files)
  - Intervention/dosing metadata

API Base: https://pk-db.com/api/v1/
Docs:     https://pk-db.com/api/v1/swagger/
Reference: Grzegorzewski et al., Nucleic Acids Research, 2022.
           https://doi.org/10.1093/nar/gkab1028

IMPORTANT NOTE ON DATA ACCESS:
  The /pkdata/outputs/ and /pkdata/timecourses/ endpoints return 0 records
  without authentication (session cookie required). This is a known limitation
  of the PK-DB public API for concentration time-series data.

  Alternative approaches implemented here:
    1. /pkdata/studies/ — study metadata with substance lists (public)
    2. Direct TSV file download for studies with licence='open'
       (files at https://pk-db.com/media/data/ without dot prefix are public)
    3. /pkdata/interventions/ — dosing data (public, no auth needed)
    4. /info_nodes/?ntype=substance — substance identifiers with ChEMBL xrefs

Usage:
    python src/fetch_pkdb.py [--max-substances 200] [--out-dir data/raw/pkdb]
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

import requests
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://pk-db.com/api/v1"
DEFAULT_OUT_DIR = Path(__file__).parent.parent / "data" / "raw" / "pkdb"
PAGE_SIZE = 100          # items per API page
REQUEST_DELAY = 0.5      # seconds between requests (be polite to API)
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0      # seconds, exponential

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_json(url: str, params: dict | None = None, session: requests.Session | None = None) -> Any:
    """
    Perform a GET request with retry logic.
    Returns parsed JSON or raises RuntimeError after max retries.
    """
    s = session or requests.Session()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = s.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as exc:
            log.warning("HTTP %s on %s (attempt %d/%d)", exc.response.status_code, url, attempt, MAX_RETRIES)
        except requests.RequestException as exc:
            log.warning("Request error on %s: %s (attempt %d/%d)", url, exc, attempt, MAX_RETRIES)
        if attempt < MAX_RETRIES:
            wait = RETRY_BACKOFF ** attempt
            log.info("Retrying in %.1f s…", wait)
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts")


def _paginate(endpoint: str, extra_params: dict | None = None, max_pages: int | None = None) -> list[dict]:
    """
    Walk all pages of a PK-DB paginated endpoint.
    PK-DB pagination format:
        { "current_page": N, "last_page": M, "data": { "count": C, "data": [...] } }

    Returns flat list of all records.
    """
    params: dict = {"format": "json", "limit": PAGE_SIZE}
    if extra_params:
        params.update(extra_params)

    url = f"{BASE_URL}/{endpoint.lstrip('/')}/"
    session = requests.Session()
    all_records: list[dict] = []

    first = _get_json(url, params=params, session=session)
    last_page = first.get("last_page", 1)
    records = first.get("data", {})
    if isinstance(records, dict):
        records = records.get("data", [])
    all_records.extend(records)

    pages = range(2, last_page + 1)
    if max_pages is not None:
        pages = range(2, min(last_page + 1, max_pages + 1))

    for page_num in tqdm(pages, desc=f"Pages of /{endpoint}", leave=False):
        time.sleep(REQUEST_DELAY)
        p = dict(params)
        p["page"] = page_num
        data = _get_json(url, params=p, session=session)
        chunk = data.get("data", {})
        if isinstance(chunk, dict):
            chunk = chunk.get("data", [])
        all_records.extend(chunk)

    return all_records


# ---------------------------------------------------------------------------
# Substance info_nodes
# ---------------------------------------------------------------------------

def fetch_substances(out_dir: Path, max_pages: int | None = None) -> list[dict]:
    """
    Fetch all PK-DB substance info_nodes.

    Each record contains:
      - sid          : PK-DB substance identifier (e.g. "caffeine", "midazolam")
      - name / label : display names
      - xrefs        : list of cross-references (chembl, chebi, pubchem, drugbank …)
      - annotations  : ontology annotations (CHEBI, NCIT …)
      - synonyms     : alternative names

    The `xrefs` field is the primary source for ChEMBL ID mapping.

    API: GET /api/v1/info_nodes/?ntype=substance
    """
    log.info("Fetching PK-DB substance info_nodes (ntype=substance)…")
    substances = _paginate("info_nodes", extra_params={"ntype": "substance"}, max_pages=max_pages)
    log.info("  → %d substance records fetched", len(substances))

    out_path = out_dir / "substances.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": "PK-DB REST API",
                "endpoint": f"{BASE_URL}/info_nodes/?ntype=substance",
                "description": "All PK-DB substance info_nodes with cross-references",
                "fields": [
                    "sid", "name", "label", "ntype", "dtype",
                    "description", "synonyms", "parents",
                    "annotations", "xrefs", "substance"
                ],
                "count": len(substances),
                "data": substances,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    log.info("  Saved → %s", out_path)
    return substances


# ---------------------------------------------------------------------------
# Concentration outputs (PK time-series)
# ---------------------------------------------------------------------------

def fetch_concentration_outputs(out_dir: Path, max_pages: int | None = None) -> list[dict]:
    """
    Fetch concentration measurement outputs from PK-DB.

    Each record represents a single PK measurement point:
      - study_sid      : PK-DB study identifier
      - substance      : substance sid
      - time           : time value (numeric string)
      - time_unit      : time unit (typically "hr")
      - value          : measured quantity (mean, median, or individual)
      - unit           : concentration unit
      - measurement_type : type of measurement (concentration, AUC, etc.)
      - tissue         : sampling compartment (blood, plasma, urine, …)
      - group_pk / individual_pk : subject grouping

    We filter for normed=true to get SI-normalised concentrations and
    collect only 'concentration' measurement_type for time-series use.

    API: GET /api/v1/pkdata/outputs/?normed=true
    """
    log.info("Fetching PK-DB concentration outputs (normed=true)…")

    # Fetch normed outputs — these are unit-normalised versions of raw measurements
    outputs = _paginate(
        "pkdata/outputs",
        extra_params={"normed": "true"},
        max_pages=max_pages,
    )
    log.info("  → %d normed output records fetched", len(outputs))

    out_path = out_dir / "outputs_normed.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": "PK-DB REST API",
                "endpoint": f"{BASE_URL}/pkdata/outputs/?normed=true",
                "description": (
                    "Normed PK measurement outputs. Each record is one measurement "
                    "point for a substance in a study. Time-series are reconstructed "
                    "by grouping on (study_sid, substance, group_pk/individual_pk)."
                ),
                "fields": [
                    "study_sid", "study_name", "output_pk", "raw_pk",
                    "normed", "substance", "substance_label",
                    "measurement_type", "measurement_type_label",
                    "time", "time_unit", "value", "mean", "median",
                    "min", "max", "sd", "se", "cv", "unit",
                    "tissue", "group_pk", "individual_pk",
                ],
                "count": len(outputs),
                "data": outputs,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    log.info("  Saved → %s", out_path)
    return outputs


# ---------------------------------------------------------------------------
# Timecourses (alternative endpoint)
# ---------------------------------------------------------------------------

def fetch_timecourses(out_dir: Path, max_pages: int | None = None) -> list[dict]:
    """
    Fetch timecourse data from PK-DB /pkdata/timecourses/ endpoint.

    Timecourses are pre-assembled time–concentration arrays per study/substance.
    This endpoint may return fewer records than /outputs/ but each record
    already has the full (time[], concentration[]) structure.

    API: GET /api/v1/pkdata/timecourses/
    """
    log.info("Fetching PK-DB timecourses…")
    tcs = _paginate("pkdata/timecourses", max_pages=max_pages)
    log.info("  → %d timecourse records fetched", len(tcs))

    out_path = out_dir / "timecourses.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": "PK-DB REST API",
                "endpoint": f"{BASE_URL}/pkdata/timecourses/",
                "description": (
                    "Pre-assembled timecourse records. Each record contains arrays of "
                    "time points and corresponding concentration values for a "
                    "substance–study combination."
                ),
                "count": len(tcs),
                "data": tcs,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    log.info("  Saved → %s", out_path)
    return tcs


# ---------------------------------------------------------------------------
# Interventions (dosing metadata)
# ---------------------------------------------------------------------------

def fetch_interventions(out_dir: Path, max_pages: int | None = None) -> list[dict]:
    """
    Fetch dosing intervention records from PK-DB.

    Each record describes a dosing event:
      - substance / substance_label
      - route (oral, iv, …)
      - form (tablet, solution, …)
      - application (single-dose, multiple-dose)
      - dose value and unit
      - study_sid for linking to outputs

    API: GET /api/v1/pkdata/interventions/
    """
    log.info("Fetching PK-DB interventions (dosing metadata)…")
    interventions = _paginate(
        "pkdata/interventions",
        extra_params={"normed": "true"},
        max_pages=max_pages,
    )
    log.info("  → %d intervention records fetched", len(interventions))

    out_path = out_dir / "interventions.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": "PK-DB REST API",
                "endpoint": f"{BASE_URL}/pkdata/interventions/?normed=true",
                "description": (
                    "Dosing interventions (unit-normalised). Links study to substance "
                    "administration details."
                ),
                "fields": [
                    "study_sid", "study_name", "intervention_pk", "normed",
                    "substance", "substance_label",
                    "route", "route_label", "form", "form_label",
                    "application", "application_label",
                    "measurement_type", "value", "unit",
                    "time", "time_unit",
                ],
                "count": len(interventions),
                "data": interventions,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    log.info("  Saved → %s", out_path)
    return interventions


# ---------------------------------------------------------------------------
# Studies metadata
# ---------------------------------------------------------------------------

def fetch_studies(out_dir: Path, max_pages: int | None = None) -> list[dict]:
    """
    Fetch study-level metadata from PK-DB.

    Study records link study_sid to reference/publication metadata.

    API: GET /api/v1/studies/
    """
    log.info("Fetching PK-DB studies metadata (basic)…")
    studies = _paginate("studies", max_pages=max_pages)
    log.info("  → %d study records fetched", len(studies))

    out_path = out_dir / "studies.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": "PK-DB REST API",
                "endpoint": f"{BASE_URL}/studies/",
                "description": "Study-level metadata (title, PubMed reference, etc.)",
                "count": len(studies),
                "data": studies,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    log.info("  Saved → %s", out_path)
    return studies


def fetch_pkdata_studies(out_dir: Path, max_pages: int | None = None) -> list[dict]:
    """
    Fetch study metadata from the pkdata/studies endpoint.

    This endpoint returns richer study information including:
      - sid           : study identifier (PKDBXXXXX)
      - name          : study name (AuthorYear)
      - licence       : 'open' or 'closed'
      - access        : 'public' or 'private'
      - substances    : list of substance names in this study
      - reference_pmid: PubMed ID
      - reference_title: publication title

    Unlike pkdata/outputs, this endpoint is publicly accessible without
    authentication and contains 803+ studies.

    API: GET /api/v1/pkdata/studies/
    """
    log.info("Fetching PK-DB pkdata studies (with licence info)…")
    studies = _paginate("pkdata/studies", max_pages=max_pages)
    log.info("  → %d pkdata study records fetched", len(studies))

    # Report licence breakdown
    open_studies = [s for s in studies if s.get("licence") == "open"]
    closed_studies = [s for s in studies if s.get("licence") == "closed"]
    log.info("    licence=open:   %d studies", len(open_studies))
    log.info("    licence=closed: %d studies", len(closed_studies))

    out_path = out_dir / "pkdata_studies.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": "PK-DB REST API",
                "endpoint": f"{BASE_URL}/pkdata/studies/",
                "description": (
                    "Study metadata with licence and substance information. "
                    "Studies with licence='open' may have publicly accessible "
                    "TSV data files at https://pk-db.com/media/data/"
                ),
                "fields": [
                    "sid", "name", "licence", "access", "date",
                    "creator", "curators", "substances",
                    "reference_pmid", "reference_title", "reference_date",
                ],
                "licence_breakdown": {
                    "open": len(open_studies),
                    "closed": len(closed_studies),
                    "total": len(studies),
                },
                "count": len(studies),
                "data": studies,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    log.info("  Saved → %s", out_path)
    return studies


def fetch_open_study_tsvs(
    pkdata_studies: list[dict],
    out_dir: Path,
    max_studies: int = 30,
) -> list[dict]:
    """
    Attempt to download PK timecourse TSV files for open-licence studies.

    PK-DB stores concentration-time data as TSV files referenced in study
    metadata. Files with no dot-prefix are publicly accessible; dot-prefixed
    files (.filename.tsv) are restricted (require auth).

    For open-licence studies, the API returns TSV URLs that may be publicly
    accessible. This function:
      1. Filters studies with licence='open'
      2. Requests the _studies internal endpoint for TSV file URLs
         (if accessible without auth)
      3. Downloads and parses TSV files to extract concentration time-series

    NOTE: Access depends on server configuration. Files beginning with a dot
    (e.g., .Erp2011_Fig1.tsv) are typically restricted. Non-dot public data
    files (e.g., Erp2011_Tab1.tsv) may be accessible.

    Returns list of successfully parsed timecourse records.
    """
    open_studies = [
        s for s in pkdata_studies if s.get("licence") == "open"
    ][:max_studies]
    log.info(
        "Attempting to download TSV data for %d open-licence studies…",
        len(open_studies),
    )

    session = requests.Session()
    timecourses = []
    accessible_tsv_count = 0
    failed_count = 0

    for study in open_studies:
        sid = study.get("sid", "")
        name = study.get("name", "")
        substances = study.get("substances", [])
        pmid = study.get("reference_pmid", "")

        # Try to access the study's TSV files via the _studies detail endpoint
        time.sleep(REQUEST_DELAY)
        try:
            detail = _get_json(
                f"{BASE_URL}/_studies/{sid}/",
                params={"format": "json"},
                session=session,
            )
        except RuntimeError:
            log.debug("  Could not fetch detail for %s (auth required)", sid)
            failed_count += 1
            continue

        # Extract TSV file URLs from outputset
        output_set = detail.get("outputset", {})
        outputs = output_set.get("outputs", [])
        for output in outputs:
            source = output.get("source", "")
            if not source or not source.startswith("http"):
                continue
            if not source.endswith(".tsv"):
                continue
            # Skip dot-prefixed files (require auth)
            filename = source.split("/")[-1]
            if filename.startswith("."):
                log.debug("  Skipping restricted file: %s", filename)
                continue

            # Attempt download
            time.sleep(REQUEST_DELAY)
            try:
                resp = session.get(source, timeout=20)
                resp.raise_for_status()
                lines = resp.text.strip().splitlines()
                if len(lines) < 2:
                    continue

                # Parse TSV
                import csv
                reader = csv.DictReader(lines, delimiter="\t")
                rows = list(reader)

                # Look for time + concentration columns
                cols = [c.lower() for c in (reader.fieldnames or [])]
                time_col = next((c for c in reader.fieldnames or [] if "time" in c.lower()), None)
                conc_col = next(
                    (c for c in reader.fieldnames or []
                     if any(k in c.lower() for k in ["conc", "mean", "value"])),
                    None,
                )

                if time_col and conc_col:
                    accessible_tsv_count += 1
                    for row in rows:
                        try:
                            t = float(row[time_col])
                            c = float(row[conc_col])
                        except (ValueError, TypeError):
                            continue
                        timecourses.append({
                            "study_sid": sid,
                            "study_name": name,
                            "substance": ", ".join(substances),
                            "pmid": pmid,
                            "tsv_source": source,
                            "time": t,
                            "concentration": c,
                            "time_col_raw": time_col,
                            "conc_col_raw": conc_col,
                        })
                    log.debug(
                        "  Downloaded %s: %d rows", filename, len(rows)
                    )

            except requests.HTTPError as e:
                if e.response.status_code in (403, 404):
                    log.debug("  Access denied: %s", filename)
                else:
                    log.warning("  HTTP error downloading %s: %s", filename, e)
                failed_count += 1

    log.info(
        "  TSV downloads: %d accessible files, %d failed/restricted",
        accessible_tsv_count,
        failed_count,
    )
    log.info("  Parsed %d timecourse data points", len(timecourses))

    out_path = out_dir / "open_timecourses.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": "PK-DB media files (open-licence studies)",
                "description": (
                    "Concentration-time data parsed from publicly accessible TSV "
                    "files for open-licence studies. Note: most TSV files require "
                    "authentication (dot-prefixed). Only non-restricted files included."
                ),
                "access_note": (
                    "The pkdata/outputs and pkdata/timecourses API endpoints return "
                    "0 records without authentication. This dataset was assembled from "
                    "directly accessible TSV media files for open-licence studies only."
                ),
                "tsv_files_accessed": accessible_tsv_count,
                "tsv_files_restricted": failed_count,
                "count": len(timecourses),
                "data": timecourses,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    log.info("  Saved → %s", out_path)
    return timecourses


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Download PK-DB pilot data via REST API"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory for raw PK-DB data (default: data/raw/pkdb)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to fetch per endpoint (None = all). "
             "Use a small value (e.g. 5) for a quick smoke test.",
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Pilot mode: fetch only 3 pages per endpoint (~300 records each)",
    )
    parser.add_argument(
        "--max-studies",
        type=int,
        default=30,
        help="Max open-licence studies to attempt TSV download (default: 30)",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    max_pages = args.max_pages
    if args.pilot:
        max_pages = 3
        log.info("Running in PILOT mode (max_pages=%d)", max_pages)

    log.info("=" * 60)
    log.info("PK-DB Data Fetcher — Phase 1")
    log.info("Output directory: %s", out_dir.resolve())
    log.info("=" * 60)

    # 1. Substance catalogue (cross-refs for ID mapping)
    substances = fetch_substances(out_dir, max_pages=max_pages)

    # 2. pkdata/studies — rich study metadata with licence information
    pkdata_studies = fetch_pkdata_studies(out_dir, max_pages=max_pages)

    # 3. Attempt TSV download for open-licence studies
    #    (fallback since pkdata/outputs requires authentication)
    open_tcs = fetch_open_study_tsvs(
        pkdata_studies,
        out_dir,
        max_studies=args.max_studies,
    )

    # 4. Pre-assembled timecourses endpoint (public endpoint, returns 0 without auth)
    timecourses = fetch_timecourses(out_dir, max_pages=max_pages)

    # 5. Concentration outputs (returns 0 without auth — documented)
    outputs = fetch_concentration_outputs(out_dir, max_pages=max_pages)

    # 6. Dosing interventions
    interventions = fetch_interventions(out_dir, max_pages=max_pages)

    # 7. Study metadata (basic)
    studies = fetch_studies(out_dir, max_pages=max_pages)

    # Summary
    log.info("")
    log.info("=" * 60)
    log.info("PK-DB Download Summary")
    log.info("  Substances:           %d", len(substances))
    log.info("  pkdata Studies:       %d (open: %d)",
             len(pkdata_studies),
             len([s for s in pkdata_studies if s.get("licence") == "open"]))
    log.info("  Open TSV timecourses: %d data points", len(open_tcs))
    log.info("  Timecourses (API):    %d (0 = requires auth)", len(timecourses))
    log.info("  Outputs (API):        %d (0 = requires auth)", len(outputs))
    log.info("  Interventions:        %d", len(interventions))
    log.info("  Studies (basic):      %d", len(studies))
    log.info("=" * 60)
    if len(outputs) == 0 and len(timecourses) == 0:
        log.warning("")
        log.warning("KNOWN ISSUE: pkdata/outputs and pkdata/timecourses return 0")
        log.warning("records. These endpoints require session authentication.")
        log.warning("See DATA_FEASIBILITY.md for details and workarounds.")
    log.info("Raw data preserved unchanged in: %s", out_dir.resolve())


if __name__ == "__main__":
    main()
