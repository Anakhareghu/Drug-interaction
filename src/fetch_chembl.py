"""
fetch_chembl.py
===============
Phase 1 — ChEMBL Data Collection

Downloads drug–target interaction data from ChEMBL using the
official Python client (chembl_webresource_client).

Fetches, for a given list of ChEMBL compound IDs:
  - Drug mechanism of action (molecule_mechanism endpoint)
  - Bioactivity data (activity endpoint, binding assays)
  - Target information (target endpoint: protein name, UniProt AC, gene symbol)
  - Drug indication metadata (drug_indication endpoint)

API:    https://www.ebi.ac.uk/chembl/api/data/
Client: https://github.com/chembl/chembl_webresource_client
Reference: Mendez et al., Nucleic Acids Research, 2019.
           https://doi.org/10.1093/nar/gky1075

Usage:
    python src/fetch_chembl.py --chembl-ids CHEMBL1/CHEMBL40/CHEMBL49
    python src/fetch_chembl.py --ids-file data/processed/chembl_ids.txt
"""

import argparse
import json
import logging
import time
from pathlib import Path

from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_OUT_DIR = Path(__file__).parent.parent / "data" / "raw" / "chembl"
REQUEST_DELAY = 0.3   # seconds between ChEMBL requests

# Minimum pChEMBL value for activity records (>=5 ≈ IC50 ≤ 10 µM)
MIN_PCHEMBL = 5.0

# Assay types to include: B=Binding, F=Functional
ASSAY_TYPES = ["B", "F"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def _require_chembl_client():
    """Import chembl_webresource_client lazily and return new_client."""
    try:
        from chembl_webresource_client.new_client import new_client  # type: ignore
        return new_client
    except ImportError as exc:
        raise ImportError(
            "chembl_webresource_client is not installed.\n"
            "Install it with:  pip install chembl-webresource-client"
        ) from exc


# ---------------------------------------------------------------------------
# Mechanism of action
# ---------------------------------------------------------------------------

def fetch_mechanisms(chembl_ids: list[str], out_dir: Path) -> list[dict]:
    """
    Fetch drug mechanism-of-action records from ChEMBL molecule_mechanism endpoint.

    Each record links a compound to its target via a mechanism type
    (e.g. "INHIBITOR", "AGONIST") and provides:
      - molecule_chembl_id
      - target_chembl_id
      - mechanism_of_action
      - action_type
      - direct_interaction (bool)
      - molecular_mechanism (bool)

    This is curated data from the ChEMBL drugs dataset.
    """
    nc = _require_chembl_client()
    log.info("Fetching ChEMBL mechanisms for %d compounds…", len(chembl_ids))

    mechanisms = []
    mechanism_api = nc.mechanism

    for cid in tqdm(chembl_ids, desc="Mechanisms"):
        try:
            records = list(
                mechanism_api.filter(molecule_chembl_id=cid).only(
                    [
                        "molecule_chembl_id",
                        "target_chembl_id",
                        "target_name",
                        "mechanism_of_action",
                        "action_type",
                        "direct_interaction",
                        "molecular_mechanism",
                        "mechanism_comment",
                        "selectivity_comment",
                    ]
                )
            )
            mechanisms.extend(records)
        except Exception as exc:
            log.warning("Mechanism fetch failed for %s: %s", cid, exc)
        time.sleep(REQUEST_DELAY)

    log.info("  → %d mechanism records", len(mechanisms))
    return mechanisms


# ---------------------------------------------------------------------------
# Bioactivity records
# ---------------------------------------------------------------------------

def fetch_activities(chembl_ids: list[str], out_dir: Path) -> list[dict]:
    """
    Fetch bioactivity records (binding/functional assays) from ChEMBL.

    Filters applied:
      - molecule_chembl_id in chembl_ids
      - pchembl_value >= MIN_PCHEMBL  (≥5 ≈ IC50/Ki/Kd ≤ 10 µM)
      - assay_type in ("B", "F")     (Binding, Functional)

    Each record contains:
      - molecule_chembl_id
      - target_chembl_id
      - assay_chembl_id
      - assay_type
      - standard_type   (e.g. "IC50", "Ki", "Kd")
      - standard_value
      - standard_units
      - pchembl_value
      - target_organism
    """
    nc = _require_chembl_client()
    log.info(
        "Fetching ChEMBL activities (pChEMBL >= %.1f, assay_type in %s)…",
        MIN_PCHEMBL,
        ASSAY_TYPES,
    )

    activity_api = nc.activity
    activities = []
    fields = [
        "molecule_chembl_id",
        "target_chembl_id",
        "assay_chembl_id",
        "assay_type",
        "assay_description",
        "standard_type",
        "standard_value",
        "standard_units",
        "pchembl_value",
        "target_organism",
        "document_chembl_id",
        "data_validity_comment",
    ]

    for cid in tqdm(chembl_ids, desc="Activities"):
        try:
            for atype in ASSAY_TYPES:
                records = list(
                    activity_api.filter(
                        molecule_chembl_id=cid,
                        pchembl_value__gte=str(MIN_PCHEMBL),
                        assay_type=atype,
                    ).only(fields)
                )
                activities.extend(records)
        except Exception as exc:
            log.warning("Activity fetch failed for %s: %s", cid, exc)
        time.sleep(REQUEST_DELAY)

    log.info("  → %d activity records", len(activities))
    return activities


# ---------------------------------------------------------------------------
# Target information
# ---------------------------------------------------------------------------

def fetch_targets(target_ids: list[str], out_dir: Path) -> list[dict]:
    """
    Fetch target metadata for a list of ChEMBL target IDs.

    Each target record contains:
      - target_chembl_id
      - pref_name           (protein preferred name)
      - target_type         (SINGLE PROTEIN, PROTEIN COMPLEX, …)
      - organism
      - target_components   (list of proteins with UniProt ACs, gene names)

    The target_components[].accession field gives the UniProt AC,
    which is the canonical protein identifier for bipartite graph edges.
    """
    if not target_ids:
        log.info("No target IDs to fetch.")
        return []

    nc = _require_chembl_client()
    target_api = nc.target
    unique_targets = list(set(target_ids))
    log.info("Fetching target metadata for %d unique targets…", len(unique_targets))

    targets = []
    fields = [
        "target_chembl_id",
        "pref_name",
        "target_type",
        "organism",
        "target_components",
    ]

    BATCH = 20
    for i in tqdm(range(0, len(unique_targets), BATCH), desc="Targets"):
        batch = unique_targets[i : i + BATCH]
        try:
            records = list(
                target_api.filter(target_chembl_id__in=batch).only(fields)
            )
            targets.extend(records)
        except Exception as exc:
            log.warning("Target fetch failed for batch %s: %s", batch[:3], exc)
        time.sleep(REQUEST_DELAY)

    log.info("  → %d target records", len(targets))
    return targets


# ---------------------------------------------------------------------------
# Drug indication
# ---------------------------------------------------------------------------

def fetch_drug_indications(chembl_ids: list[str], out_dir: Path) -> list[dict]:
    """
    Fetch drug indication records from ChEMBL drug_indication endpoint.

    Provides therapeutic area and indication information:
      - molecule_chembl_id
      - indication_refs (MeSH, EFO disease terms)
      - efo_term / efo_id (disease ontology label)
      - mesh_heading / mesh_id (MeSH disease label)
      - max_phase_for_ind (highest clinical phase reached for this indication)
    """
    nc = _require_chembl_client()
    log.info("Fetching drug indications…")
    indication_api = nc.drug_indication
    indications = []

    for cid in tqdm(chembl_ids, desc="Indications"):
        try:
            records = list(
                indication_api.filter(molecule_chembl_id=cid).only(
                    [
                        "molecule_chembl_id",
                        "efo_term",
                        "efo_id",
                        "mesh_heading",
                        "mesh_id",
                        "max_phase_for_ind",
                        "indication_refs",
                    ]
                )
            )
            indications.extend(records)
        except Exception as exc:
            log.warning("Indication fetch failed for %s: %s", cid, exc)
        time.sleep(REQUEST_DELAY)

    log.info("  → %d indication records", len(indications))
    return indications


# ---------------------------------------------------------------------------
# Molecule / compound info
# ---------------------------------------------------------------------------

def fetch_molecules(chembl_ids: list[str], out_dir: Path) -> list[dict]:
    """
    Fetch compound-level metadata for the given ChEMBL IDs.

    Each record contains:
      - molecule_chembl_id
      - pref_name
      - max_phase (highest clinical trial phase reached)
      - molecule_type (Small molecule, Protein, Antibody, …)
      - molecule_properties (MW, LogP, …)
      - molecule_structures (canonical SMILES, InChIKey)
      - drug_warnings (withdrawal / safety flags)
    """
    nc = _require_chembl_client()
    log.info("Fetching molecule metadata for %d compounds…", len(chembl_ids))
    molecule_api = nc.molecule
    molecules = []

    BATCH = 20
    for i in tqdm(range(0, len(chembl_ids), BATCH), desc="Molecules"):
        batch = chembl_ids[i : i + BATCH]
        try:
            records = list(
                molecule_api.filter(molecule_chembl_id__in=batch).only(
                    [
                        "molecule_chembl_id",
                        "pref_name",
                        "max_phase",
                        "molecule_type",
                        "molecule_properties",
                        "molecule_structures",
                        "drug_warnings",
                    ]
                )
            )
            molecules.extend(records)
        except Exception as exc:
            log.warning("Molecule fetch failed for batch %s…: %s", batch[:3], exc)
        time.sleep(REQUEST_DELAY)

    log.info("  → %d molecule records", len(molecules))
    return molecules


# ---------------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------------

def _save_json(data: list[dict], path: Path, meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**meta, "count": len(data), "data": data}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    log.info("  Saved %d records → %s", len(data), path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_chembl_fetch(
    chembl_ids: list[str],
    out_dir: Path,
) -> dict[str, list[dict]]:
    """
    Fetch all ChEMBL data for a list of ChEMBL compound IDs.
    Returns a dict of {data_type: records}.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, list[dict]] = {}

    # 1. Molecule metadata
    molecules = fetch_molecules(chembl_ids, out_dir)
    _save_json(
        molecules,
        out_dir / "molecules.json",
        {
            "source": "ChEMBL REST API (chembl_webresource_client)",
            "endpoint": "molecule",
            "description": "Compound metadata: name, max_phase, SMILES, InChIKey",
            "fields": [
                "molecule_chembl_id", "pref_name", "max_phase",
                "molecule_type", "molecule_properties", "molecule_structures",
            ],
            "query_ids": chembl_ids,
        },
    )
    results["molecules"] = molecules

    # 2. Mechanisms of action (curated drug target data)
    mechanisms = fetch_mechanisms(chembl_ids, out_dir)
    _save_json(
        mechanisms,
        out_dir / "mechanisms.json",
        {
            "source": "ChEMBL REST API (chembl_webresource_client)",
            "endpoint": "mechanism",
            "description": (
                "Curated drug mechanism-of-action records. "
                "Primary source for drug–target edges."
            ),
            "fields": [
                "molecule_chembl_id", "target_chembl_id", "target_name",
                "mechanism_of_action", "action_type", "direct_interaction",
            ],
            "query_ids": chembl_ids,
        },
    )
    results["mechanisms"] = mechanisms

    # 3. Bioactivities (binding/functional assays)
    activities = fetch_activities(chembl_ids, out_dir)
    _save_json(
        activities,
        out_dir / "activities.json",
        {
            "source": "ChEMBL REST API (chembl_webresource_client)",
            "endpoint": "activity",
            "description": (
                f"Bioactivity records filtered: pChEMBL >= {MIN_PCHEMBL}, "
                f"assay_type in {ASSAY_TYPES}. Used to supplement mechanism data."
            ),
            "fields": [
                "molecule_chembl_id", "target_chembl_id", "assay_type",
                "standard_type", "standard_value", "standard_units",
                "pchembl_value", "target_organism",
            ],
            "query_ids": chembl_ids,
            "filters": {
                "pchembl_value__gte": MIN_PCHEMBL,
                "assay_types": ASSAY_TYPES,
            },
        },
    )
    results["activities"] = activities

    # 4. Unique targets from mechanism + activity records
    all_target_ids = list(
        {
            r["target_chembl_id"]
            for r in (mechanisms + activities)
            if r.get("target_chembl_id")
        }
    )
    targets = fetch_targets(all_target_ids, out_dir)
    _save_json(
        targets,
        out_dir / "targets.json",
        {
            "source": "ChEMBL REST API (chembl_webresource_client)",
            "endpoint": "target",
            "description": (
                "Target metadata for all unique targets from mechanisms + activities. "
                "target_components[].accession gives UniProt AC for bipartite graph."
            ),
            "fields": [
                "target_chembl_id", "pref_name", "target_type",
                "organism", "target_components",
            ],
        },
    )
    results["targets"] = targets

    # 5. Drug indications
    indications = fetch_drug_indications(chembl_ids, out_dir)
    _save_json(
        indications,
        out_dir / "drug_indications.json",
        {
            "source": "ChEMBL REST API (chembl_webresource_client)",
            "endpoint": "drug_indication",
            "description": "Therapeutic indications and disease ontology terms.",
            "fields": [
                "molecule_chembl_id", "efo_term", "efo_id",
                "mesh_heading", "mesh_id", "max_phase_for_ind",
            ],
            "query_ids": chembl_ids,
        },
    )
    results["indications"] = indications

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Download ChEMBL drug-target data"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--chembl-ids",
        type=str,
        help="Slash-separated ChEMBL IDs, e.g. CHEMBL1/CHEMBL40/CHEMBL49",
    )
    group.add_argument(
        "--ids-file",
        type=Path,
        help="File with one ChEMBL ID per line",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory (default: data/raw/chembl)",
    )
    args = parser.parse_args()

    if args.chembl_ids:
        chembl_ids = [x.strip() for x in args.chembl_ids.split("/") if x.strip()]
    else:
        chembl_ids = [
            line.strip()
            for line in args.ids_file.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]

    log.info("=" * 60)
    log.info("ChEMBL Data Fetcher — Phase 1")
    log.info("Input IDs:        %d", len(chembl_ids))
    log.info("Output directory: %s", args.out_dir.resolve())
    log.info("=" * 60)

    results = run_chembl_fetch(chembl_ids, args.out_dir)

    log.info("")
    log.info("=" * 60)
    log.info("ChEMBL Download Summary")
    for k, v in results.items():
        log.info("  %-20s %d records", k + ":", len(v))
    log.info("=" * 60)


if __name__ == "__main__":
    main()
