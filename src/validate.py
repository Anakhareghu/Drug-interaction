"""
validate.py
===========
Phase 1 — Data Validation

Validates the raw and processed data for Phase 1:
  1. Raw PK-DB data (substances, outputs, interventions)
  2. Raw ChEMBL data (molecules, mechanisms, targets)
  3. ID mapping table
  4. Pilot matched dataset

Validation checks:
  - File existence and non-empty
  - Required field presence
  - Data type correctness (numeric times, concentrations)
  - ChEMBL ID format (CHEMBL[0-9]+)
  - Mapping consistency
  - Pilot dataset integrity

Prints a structured validation report to stdout.

Usage:
    python src/validate.py
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

RAW_PKDB = Path(__file__).parent.parent / "data" / "raw" / "pkdb"
RAW_CHEMBL = Path(__file__).parent.parent / "data" / "raw" / "chembl"
PROCESSED = Path(__file__).parent.parent / "data" / "processed"

CHEMBL_ID_RE = re.compile(r"^CHEMBL\d+$", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


class ValidationResult:
    """Accumulates pass/warn/fail checks."""

    def __init__(self, name: str):
        self.name = name
        self.checks: list[tuple[str, str, str]] = []  # (level, label, detail)

    def ok(self, label: str, detail: str = "") -> None:
        self.checks.append(("[OK] ", label, detail))

    def warn(self, label: str, detail: str = "") -> None:
        self.checks.append(("[WARN]", label, detail))

    def fail(self, label: str, detail: str = "") -> None:
        self.checks.append(("[FAIL]", label, detail))

    @property
    def n_failures(self) -> int:
        return sum(1 for lvl, _, _ in self.checks if lvl == "[FAIL]")

    @property
    def n_warnings(self) -> int:
        return sum(1 for lvl, _, _ in self.checks if lvl == "[WARN]")

    def report(self) -> str:
        lines = [f"\n{'─' * 55}", f"  {self.name}", f"{'─' * 55}"]
        for lvl, label, detail in self.checks:
            suffix = f"  ({detail})" if detail else ""
            lines.append(f"  {lvl} {label}{suffix}")
        status = "PASS" if self.n_failures == 0 else "FAIL"
        lines.append(f"  → {status}: {self.n_failures} failures, {self.n_warnings} warnings")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_pkdb_substances() -> ValidationResult:
    vr = ValidationResult("PK-DB substances.json")
    payload = _load_json(RAW_PKDB / "substances.json")

    if payload is None:
        vr.fail("File exists", "substances.json not found — run fetch_pkdb.py")
        return vr
    vr.ok("File exists")

    records = payload.get("data", [])
    count = payload.get("count", 0)
    vr.ok("Record count", f"{len(records)} records (count field: {count})")

    if not records:
        vr.fail("Non-empty data", "data array is empty")
        return vr
    vr.ok("Non-empty data")

    # Check required fields
    req_fields = ["sid", "name", "label", "ntype", "xrefs", "annotations"]
    sample = records[:10]
    for field in req_fields:
        missing = sum(1 for r in sample if field not in r)
        if missing:
            vr.warn(f"Field '{field}'", f"missing in {missing}/10 sample records")
        else:
            vr.ok(f"Field '{field}' present")

    # Check ChEMBL xrefs
    with_chembl = sum(
        1 for r in records
        if any(x.get("name") == "chembl" for x in (r.get("xrefs") or []))
    )
    pct = 100 * with_chembl / max(len(records), 1)
    if pct < 10:
        vr.warn("ChEMBL xrefs", f"{with_chembl}/{len(records)} ({pct:.1f}%) have ChEMBL xref")
    else:
        vr.ok("ChEMBL xrefs", f"{with_chembl}/{len(records)} ({pct:.1f}%) have ChEMBL xref")

    # Validate ChEMBL ID format
    bad_ids = 0
    for r in records:
        for xref in (r.get("xrefs") or []):
            if xref.get("name") == "chembl":
                acc = xref.get("accession", "")
                if acc and not CHEMBL_ID_RE.match(acc):
                    bad_ids += 1
    if bad_ids:
        vr.warn("ChEMBL ID format", f"{bad_ids} xrefs do not match CHEMBL[0-9]+")
    else:
        vr.ok("ChEMBL ID format", "all match CHEMBL[0-9]+")

    return vr


def validate_pkdb_outputs() -> ValidationResult:
    vr = ValidationResult("PK-DB outputs_normed.json")
    payload = _load_json(RAW_PKDB / "outputs_normed.json")

    if payload is None:
        vr.warn("File exists", "outputs_normed.json not found — PK time-series may be empty")
        return vr
    vr.ok("File exists")

    records = payload.get("data", [])
    vr.ok("Record count", f"{len(records)}")

    if not records:
        vr.warn("Non-empty data", "outputs_normed.json has no records (check API availability)")
        return vr

    # Check concentration records
    conc_records = [r for r in records if "concentration" in (r.get("measurement_type") or "")]
    vr.ok("Concentration records", f"{len(conc_records)} / {len(records)}")

    # Check required fields
    req = ["study_sid", "substance", "time", "measurement_type"]
    sample = records[:20]
    for field in req:
        missing = sum(1 for r in sample if not r.get(field))
        level = vr.warn if missing > 5 else vr.ok
        level(f"Field '{field}'", f"{missing}/20 sample records missing value")

    # Check numeric time values
    bad_time = 0
    for r in records[:100]:
        t = r.get("time")
        if t is not None:
            try:
                float(t)
            except (ValueError, TypeError):
                bad_time += 1
    if bad_time:
        vr.warn("Numeric time values", f"{bad_time}/100 sample records have non-numeric time")
    else:
        vr.ok("Numeric time values", "all sample records OK")

    return vr


def validate_chembl_data() -> ValidationResult:
    vr = ValidationResult("ChEMBL raw data")

    for fname, required_fields in [
        ("mechanisms.json", ["molecule_chembl_id", "target_chembl_id", "action_type"]),
        ("activities.json", ["molecule_chembl_id", "target_chembl_id", "pchembl_value"]),
        ("targets.json", ["target_chembl_id", "pref_name", "target_type"]),
        ("molecules.json", ["molecule_chembl_id", "pref_name", "max_phase"]),
    ]:
        payload = _load_json(RAW_CHEMBL / fname)
        if payload is None:
            vr.warn(f"{fname} exists", f"Not found — run fetch_chembl.py")
            continue

        records = payload.get("data", [])
        vr.ok(f"{fname}", f"{len(records)} records")

        if not records:
            vr.warn(f"{fname} non-empty", "No records found")
            continue

        for field in required_fields:
            missing = sum(1 for r in records if not r.get(field))
            level = vr.warn if missing > len(records) * 0.2 else vr.ok
            level(f"  {fname} field '{field}'", f"{missing}/{len(records)} missing")

    # Validate ChEMBL ID format in mechanisms
    mech_payload = _load_json(RAW_CHEMBL / "mechanisms.json")
    if mech_payload:
        bad = sum(
            1 for r in mech_payload.get("data", [])
            if r.get("molecule_chembl_id") and not CHEMBL_ID_RE.match(r["molecule_chembl_id"])
        )
        if bad:
            vr.warn("ChEMBL ID format in mechanisms", f"{bad} bad IDs")
        else:
            vr.ok("ChEMBL ID format in mechanisms")

    return vr


def validate_mapping_table() -> ValidationResult:
    vr = ValidationResult("ID mapping table (id_mapping_table.csv)")
    df = _load_csv(PROCESSED / "id_mapping_table.csv")

    if df is None:
        vr.warn("File exists", "Not found — run map_identifiers.py")
        return vr
    vr.ok("File exists")
    vr.ok("Row count", str(len(df)))

    # Required columns
    req_cols = ["pkdb_sid", "pkdb_label", "chembl_id", "mapping_method", "confidence"]
    for col in req_cols:
        if col not in df.columns:
            vr.fail(f"Column '{col}'", "missing from CSV")
        else:
            vr.ok(f"Column '{col}'")

    if "chembl_id" not in df.columns:
        return vr

    mapped = df["chembl_id"].notna().sum()
    pct = 100 * mapped / max(len(df), 1)
    vr.ok("Mapped substances", f"{mapped}/{len(df)} ({pct:.1f}%)")

    # Validate ChEMBL IDs
    if "chembl_id" in df.columns:
        bad_ids = df[df["chembl_id"].notna()]["chembl_id"].apply(
            lambda x: not CHEMBL_ID_RE.match(str(x))
        ).sum()
        if bad_ids:
            vr.warn("ChEMBL ID format", f"{bad_ids} non-conforming IDs")
        else:
            vr.ok("ChEMBL ID format", "all match CHEMBL[0-9]+")

    # Duplicate check
    dups = df[df["chembl_id"].notna()].duplicated(subset=["pkdb_sid", "chembl_id"]).sum()
    if dups:
        vr.warn("Duplicate pkdb_sid–chembl_id pairs", f"{dups} duplicates found")
    else:
        vr.ok("No duplicate mappings")

    # Methods breakdown
    if "mapping_method" in df.columns:
        counts = df["mapping_method"].value_counts()
        for method, count in counts.items():
            vr.ok(f"  mapping_method={method}", str(count))

    return vr


def validate_pilot_dataset() -> ValidationResult:
    vr = ValidationResult("Pilot matched dataset")

    # Check pilot_matched.csv
    pk_df = _load_csv(PROCESSED / "pilot_matched.csv")
    if pk_df is None:
        vr.warn("pilot_matched.csv exists", "Not found — run build_pilot.py")
    else:
        vr.ok("pilot_matched.csv exists", f"{len(pk_df)} rows")

        req_cols = ["pkdb_sid", "time_hr", "conc"]
        for col in req_cols:
            if col in pk_df.columns:
                vr.ok(f"Column '{col}' present")
            else:
                vr.fail(f"Column '{col}'", "missing")

        if "time_hr" in pk_df.columns:
            non_numeric = pk_df["time_hr"].isna().sum()
            neg = (pk_df["time_hr"] < 0).sum()
            vr.ok("time_hr non-null", f"{non_numeric} nulls") if non_numeric == 0 else vr.warn("time_hr nulls", str(non_numeric))
            vr.ok("time_hr non-negative") if neg == 0 else vr.warn("time_hr negative values", str(neg))

        if "conc" in pk_df.columns:
            neg_conc = (pk_df["conc"] < 0).sum()
            vr.ok("conc non-negative") if neg_conc == 0 else vr.warn("Negative concentrations", str(neg_conc))

        n_drugs = pk_df["pkdb_sid"].nunique() if "pkdb_sid" in pk_df.columns else 0
        vr.ok("Unique drugs in pilot", str(n_drugs))

    # Check pilot_summary.csv
    summary_df = _load_csv(PROCESSED / "pilot_summary.csv")
    if summary_df is None:
        vr.warn("pilot_summary.csv exists", "Not found")
    else:
        vr.ok("pilot_summary.csv exists", f"{len(summary_df)} drugs")
        if "n_targets" in summary_df.columns:
            no_targets = (summary_df["n_targets"] == 0).sum()
            if no_targets:
                vr.warn("Drugs without targets in summary", str(no_targets))
            else:
                vr.ok("All pilot drugs have targets")

    # Check pilot_targets.csv
    targets_df = _load_csv(PROCESSED / "pilot_targets.csv")
    if targets_df is None:
        vr.warn("pilot_targets.csv exists", "Not found")
    else:
        vr.ok("pilot_targets.csv exists", f"{len(targets_df)} drug–target edges")

    return vr


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    # Set stdout to UTF-8 to handle any remaining unicode
    import io
    import sys
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # In some environments stdout may not have a buffer

    print("\n" + "=" * 55)
    print("  Phase 1 Data Validation Report")
    print("=" * 55)

    validators = [
        validate_pkdb_substances,
        validate_pkdb_outputs,
        validate_chembl_data,
        validate_mapping_table,
        validate_pilot_dataset,
    ]

    total_failures = 0
    total_warnings = 0
    for validate_fn in validators:
        result = validate_fn()
        print(result.report())
        total_failures += result.n_failures
        total_warnings += result.n_warnings

    print("\n" + "=" * 55)
    print(f"  Overall: {total_failures} failures, {total_warnings} warnings")
    if total_failures == 0:
        print("  ✅ All validation checks passed (or warned).")
    else:
        print("  ❌ Validation completed with failures. See above.")
    print("=" * 55 + "\n")

    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
