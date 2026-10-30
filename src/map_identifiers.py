"""
map_identifiers.py
==================
Phase 1 — Cross-Database Identifier Mapping

Maps PK-DB substances to ChEMBL compound IDs using a reliable,
hierarchy-based approach that avoids fuzzy drug-name matching.

Mapping strategy (applied in priority order):
  1. Direct ChEMBL xref in PK-DB substance info_node
       → PK-DB substance.xrefs where name == "chembl"
       → MOST RELIABLE: curated by PK-DB maintainers
  2. InChIKey lookup via ChEMBL molecule API
       → PK-DB substance.annotations where collection == "inchikey"
       → chembl.molecule.filter(molecule_structures__standard_inchi_key=inchikey)
       → HIGH CONFIDENCE: InChIKey is a structural identifier
  3. CHEBI ID lookup via ChEMBL
       → PK-DB substance.annotations where collection == "chebi"
       → chembl.molecule.filter(molecule_synonyms__syn_type="CHEBI")
       → MEDIUM CONFIDENCE: curated ontology cross-reference
  4. NOT USED: fuzzy name matching (unreliable, excluded per specification)

Output:
  data/processed/id_mapping_table.csv
    Columns: pkdb_sid, pkdb_label, chembl_id, mapping_method, confidence,
             inchikey, chebi_id

Usage:
    python src/map_identifiers.py [--substances data/raw/pkdb/substances.json]
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Optional

import pandas as pd
from tqdm import tqdm

DEFAULT_PKDB_SUBSTANCES = (
    Path(__file__).parent.parent / "data" / "raw" / "pkdb" / "substances.json"
)
DEFAULT_OUT_DIR = Path(__file__).parent.parent / "data" / "processed"

REQUEST_DELAY = 0.3   # seconds between ChEMBL API requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Parse PK-DB substance data
# ---------------------------------------------------------------------------

def load_substances(path: Path) -> list[dict]:
    """Load PK-DB substances from saved JSON file."""
    if not path.exists():
        raise FileNotFoundError(
            f"Substances file not found: {path}\n"
            "Run  python src/fetch_pkdb.py  first."
        )
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("data", [])


def extract_xref(substance: dict, xref_name: str) -> Optional[str]:
    """
    Extract a cross-reference accession by name from a PK-DB substance record.

    PK-DB xrefs structure:
        [{"name": "chembl", "accession": "CHEMBL1234", "url": "..."}]
    """
    for xref in substance.get("xrefs", []):
        if xref.get("name", "").lower() == xref_name.lower():
            acc = xref.get("accession", "").strip()
            if acc:
                return acc
    return None


def extract_annotation(substance: dict, collection: str) -> Optional[str]:
    """
    Extract an annotation term by collection from a PK-DB substance record.

    PK-DB annotations structure:
        [{"term": "HMJIYCCIJYRONP-UHFFFAOYSA-N", "collection": "inchikey", ...}]
    """
    for ann in substance.get("annotations", []):
        if ann.get("collection", "").lower() == collection.lower():
            term = ann.get("term", "").strip()
            if term:
                return term
    return None


# ---------------------------------------------------------------------------
# ChEMBL lookup helpers
# ---------------------------------------------------------------------------

def _get_chembl_client():
    try:
        from chembl_webresource_client.new_client import new_client  # type: ignore
        return new_client
    except ImportError as exc:
        raise ImportError(
            "Install chembl_webresource_client: pip install chembl-webresource-client"
        ) from exc


def lookup_by_inchikey(inchikey: str, nc) -> Optional[str]:
    """
    Look up ChEMBL ID by InChIKey using the molecule API.
    Returns CHEMBLXXX or None.
    """
    try:
        results = list(
            nc.molecule.filter(
                molecule_structures__standard_inchi_key=inchikey
            ).only(["molecule_chembl_id"])
        )
        if results:
            return results[0].get("molecule_chembl_id")
    except Exception as exc:
        log.debug("InChIKey lookup failed for %s: %s", inchikey, exc)
    return None


def lookup_by_chebi(chebi_id: str, nc) -> Optional[str]:
    """
    Look up ChEMBL ID by CHEBI accession.
    CHEBI IDs appear in ChEMBL molecule_synonyms or cross_references.
    Returns CHEMBLXXX or None.
    """
    # Normalise: strip "CHEBI:" prefix if present
    chebi_num = chebi_id.replace("CHEBI:", "").strip()
    chebi_formatted = f"CHEBI:{chebi_num}"
    try:
        # Try cross-references / synonyms lookup
        results = list(
            nc.molecule.filter(
                molecule_synonyms__molecule_synonym__iexact=chebi_formatted
            ).only(["molecule_chembl_id"])
        )
        if results:
            return results[0].get("molecule_chembl_id")
    except Exception as exc:
        log.debug("CHEBI lookup failed for %s: %s", chebi_formatted, exc)
    return None


# ---------------------------------------------------------------------------
# Main mapping function
# ---------------------------------------------------------------------------

def build_id_mapping(
    substances: list[dict],
    use_api_fallback: bool = True,
) -> pd.DataFrame:
    """
    Build a mapping table from PK-DB substance SID to ChEMBL ID.

    Applies mapping strategy in priority order:
      1. Direct ChEMBL xref (no API call needed)
      2. InChIKey → ChEMBL API lookup
      3. CHEBI → ChEMBL API lookup

    Parameters
    ----------
    substances : list of PK-DB substance records
    use_api_fallback : if True, attempt InChIKey/CHEBI API lookups for
                       substances without direct ChEMBL xrefs

    Returns
    -------
    pd.DataFrame with columns:
      pkdb_sid, pkdb_label, chembl_id, mapping_method, confidence,
      inchikey, chebi_id, pubchem_id, pkdb_mass, pkdb_formula
    """
    nc = _get_chembl_client() if use_api_fallback else None

    rows = []
    stats = {
        "total": len(substances),
        "direct_xref": 0,
        "inchikey_lookup": 0,
        "chebi_lookup": 0,
        "unmapped": 0,
    }

    for substance in tqdm(substances, desc="Mapping substances"):
        sid = substance.get("sid", "")
        label = substance.get("label", substance.get("name", ""))
        mass = (substance.get("substance") or {}).get("mass")
        formula = (substance.get("substance") or {}).get("formula")

        # Extract available cross-references
        chembl_xref = extract_xref(substance, "chembl")
        inchikey = extract_annotation(substance, "inchikey")
        chebi_id = extract_annotation(substance, "chebi")
        if not chebi_id:
            chebi_id = extract_xref(substance, "chebi")
        pubchem_id = extract_xref(substance, "pubchem")

        # --- Strategy 1: Direct ChEMBL xref ---
        if chembl_xref:
            chembl_id = chembl_xref
            # Ensure it starts with CHEMBL
            if not chembl_id.upper().startswith("CHEMBL"):
                chembl_id = f"CHEMBL{chembl_id}"
            rows.append({
                "pkdb_sid": sid,
                "pkdb_label": label,
                "chembl_id": chembl_id.upper(),
                "mapping_method": "direct_xref",
                "confidence": "high",
                "inchikey": inchikey,
                "chebi_id": chebi_id,
                "pubchem_id": pubchem_id,
                "pkdb_mass": mass,
                "pkdb_formula": formula,
            })
            stats["direct_xref"] += 1
            continue

        if not use_api_fallback or nc is None:
            # Record as unmapped
            rows.append({
                "pkdb_sid": sid,
                "pkdb_label": label,
                "chembl_id": None,
                "mapping_method": "unmapped",
                "confidence": "none",
                "inchikey": inchikey,
                "chebi_id": chebi_id,
                "pubchem_id": pubchem_id,
                "pkdb_mass": mass,
                "pkdb_formula": formula,
            })
            stats["unmapped"] += 1
            continue

        # --- Strategy 2: InChIKey lookup ---
        chembl_id = None
        if inchikey:
            time.sleep(REQUEST_DELAY)
            chembl_id = lookup_by_inchikey(inchikey, nc)
            if chembl_id:
                rows.append({
                    "pkdb_sid": sid,
                    "pkdb_label": label,
                    "chembl_id": chembl_id,
                    "mapping_method": "inchikey_lookup",
                    "confidence": "high",
                    "inchikey": inchikey,
                    "chebi_id": chebi_id,
                    "pubchem_id": pubchem_id,
                    "pkdb_mass": mass,
                    "pkdb_formula": formula,
                })
                stats["inchikey_lookup"] += 1
                continue

        # --- Strategy 3: CHEBI ID lookup ---
        if chebi_id:
            time.sleep(REQUEST_DELAY)
            chembl_id = lookup_by_chebi(chebi_id, nc)
            if chembl_id:
                rows.append({
                    "pkdb_sid": sid,
                    "pkdb_label": label,
                    "chembl_id": chembl_id,
                    "mapping_method": "chebi_lookup",
                    "confidence": "medium",
                    "inchikey": inchikey,
                    "chebi_id": chebi_id,
                    "pubchem_id": pubchem_id,
                    "pkdb_mass": mass,
                    "pkdb_formula": formula,
                })
                stats["chebi_lookup"] += 1
                continue

        # --- Unmapped ---
        rows.append({
            "pkdb_sid": sid,
            "pkdb_label": label,
            "chembl_id": None,
            "mapping_method": "unmapped",
            "confidence": "none",
            "inchikey": inchikey,
            "chebi_id": chebi_id,
            "pubchem_id": pubchem_id,
            "pkdb_mass": mass,
            "pkdb_formula": formula,
        })
        stats["unmapped"] += 1

    df = pd.DataFrame(rows)
    _log_mapping_stats(stats, df)
    return df


def _log_mapping_stats(stats: dict, df: pd.DataFrame) -> None:
    total = stats["total"]
    mapped = total - stats["unmapped"]
    log.info("")
    log.info("=" * 55)
    log.info("Identifier Mapping Statistics")
    log.info("  Total PK-DB substances:  %d", total)
    log.info("  Mapped to ChEMBL:        %d (%.1f%%)", mapped, 100 * mapped / max(total, 1))
    log.info("    via direct xref:       %d", stats["direct_xref"])
    log.info("    via InChIKey lookup:   %d", stats["inchikey_lookup"])
    log.info("    via CHEBI lookup:      %d", stats["chebi_lookup"])
    log.info("  Unmapped:                %d (%.1f%%)", stats["unmapped"], 100 * stats["unmapped"] / max(total, 1))
    log.info("=" * 55)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Map PK-DB substances to ChEMBL IDs"
    )
    parser.add_argument(
        "--substances",
        type=Path,
        default=DEFAULT_PKDB_SUBSTANCES,
        help="Path to PK-DB substances.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory for mapping table",
    )
    parser.add_argument(
        "--no-api-fallback",
        action="store_true",
        help="Disable InChIKey/CHEBI API fallback (only use direct xrefs)",
    )
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("Identifier Mapper — Phase 1")
    log.info("Substances file: %s", args.substances)
    log.info("=" * 60)

    substances = load_substances(args.substances)
    log.info("Loaded %d substances from PK-DB", len(substances))

    # Filter to substances with actual chemical identity (exclude abstract/mixture nodes)
    # These are substances where mass or formula is defined, or they have xrefs
    definite = [
        s for s in substances
        if s.get("xrefs") or (s.get("substance") or {}).get("mass") or
           any(a.get("collection") == "inchikey" for a in s.get("annotations", []))
    ]
    log.info("Substances with resolvable chemical identity: %d / %d", len(definite), len(substances))

    mapping_df = build_id_mapping(definite, use_api_fallback=not args.no_api_fallback)

    # Save outputs
    args.out_dir.mkdir(parents=True, exist_ok=True)

    out_csv = args.out_dir / "id_mapping_table.csv"
    mapping_df.to_csv(out_csv, index=False)
    log.info("Mapping table saved → %s", out_csv)

    # Save just the ChEMBL IDs for fetching
    mapped_ids = mapping_df[mapping_df["chembl_id"].notna()]["chembl_id"].unique().tolist()
    ids_file = args.out_dir / "chembl_ids.txt"
    ids_file.write_text("\n".join(sorted(mapped_ids)))
    log.info("ChEMBL IDs file saved → %s (%d IDs)", ids_file, len(mapped_ids))

    # Summary by method
    log.info("\nMapping method breakdown:")
    method_counts = mapping_df["mapping_method"].value_counts()
    for method, count in method_counts.items():
        log.info("  %-25s %d", method, count)


if __name__ == "__main__":
    main()
