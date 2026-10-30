"""
build_pilot.py
==============
Phase 1 — Pilot Dataset Assembly

Assembles the matched pilot dataset by joining:
  - PK-DB concentration time-series (from outputs_normed.json)
  - ChEMBL drug-target pairs (from mechanisms.json + activities.json)
  - Identifier mapping table (from id_mapping_table.csv)

A drug is considered "usable" for the downstream project if it has:
  1. At least MIN_PK_TIMEPOINTS concentration measurements (time + value)
  2. At least 1 ChEMBL target link (mechanism or activity)

Outputs:
  data/processed/pilot_matched.csv     — one row per (drug, timepoint)
  data/processed/pilot_summary.csv     — one row per drug, with counts
  data/processed/pilot_targets.csv     — drug–target edges for bipartite graph
  outputs/tables/feasibility_summary.csv
  outputs/figures/pk_coverage.png      — PK timepoint coverage plot
  outputs/figures/target_network.png   — target degree distribution

Usage:
    python src/build_pilot.py
"""

import argparse
import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RAW_PKDB = Path(__file__).parent.parent / "data" / "raw" / "pkdb"
RAW_CHEMBL = Path(__file__).parent.parent / "data" / "raw" / "chembl"
PROCESSED = Path(__file__).parent.parent / "data" / "processed"
FIGURES = Path(__file__).parent.parent / "outputs" / "figures"
TABLES = Path(__file__).parent.parent / "outputs" / "tables"

# Minimum timepoints required for a usable PK trajectory
MIN_PK_TIMEPOINTS = 4

# Measurement types that represent a PK concentration time-series
CONCENTRATION_MTYPES = {
    "concentration",
    "concentration-ss",
    "concentration-unbound",
}

# ---------------------------------------------------------------------------
# Load raw data
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        log.warning("File not found: %s", path)
        return []
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("data", [])


def load_all_data() -> dict:
    log.info("Loading raw data…")
    return {
        "outputs": _load_json(RAW_PKDB / "outputs_normed.json"),
        "timecourses": _load_json(RAW_PKDB / "timecourses.json"),
        "interventions": _load_json(RAW_PKDB / "interventions.json"),
        "substances": _load_json(RAW_PKDB / "substances.json"),
        "mechanisms": _load_json(RAW_CHEMBL / "mechanisms.json"),
        "activities": _load_json(RAW_CHEMBL / "activities.json"),
        "targets": _load_json(RAW_CHEMBL / "targets.json"),
        "mapping": None,  # loaded separately as DataFrame
    }


def load_mapping() -> pd.DataFrame:
    path = PROCESSED / "id_mapping_table.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"ID mapping table not found: {path}\n"
            "Run  python src/map_identifiers.py  first."
        )
    df = pd.read_csv(path)
    log.info("  Loaded mapping table: %d rows", len(df))
    return df


# ---------------------------------------------------------------------------
# Build PK time-series dataframe
# ---------------------------------------------------------------------------

def build_pk_dataframe(outputs: list[dict]) -> pd.DataFrame:
    """
    Convert PK-DB output records to a tidy dataframe.

    Filters for concentration-type measurements with:
      - a numeric time value
      - a numeric concentration value (value or mean)
      - a substance identifier
    """
    rows = []
    for rec in outputs:
        mtype = rec.get("measurement_type", "") or ""
        # Include concentration types
        if not any(ct in mtype for ct in ["concentration", "conc"]):
            continue

        # Time
        try:
            t = float(rec.get("time") or rec.get("time_start") or "nan")
        except (ValueError, TypeError):
            continue
        if np.isnan(t) or t < 0:
            continue

        # Concentration value (prefer mean, then value)
        conc = rec.get("mean") or rec.get("value")
        try:
            conc = float(conc)
        except (ValueError, TypeError):
            continue
        if np.isnan(conc) or conc < 0:
            continue

        substance = rec.get("substance") or ""
        if not substance:
            continue

        rows.append({
            "study_sid": rec.get("study_sid", ""),
            "pkdb_sid": substance,
            "substance_label": rec.get("substance_label", substance),
            "time_hr": t,
            "conc": conc,
            "conc_unit": rec.get("unit", ""),
            "time_unit": rec.get("time_unit", ""),
            "measurement_type": mtype,
            "group_pk": rec.get("group_pk"),
            "individual_pk": rec.get("individual_pk"),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        log.warning("No PK concentration records found in outputs.")
        return df

    log.info("  PK records: %d rows, %d unique substances",
             len(df), df["pkdb_sid"].nunique())
    return df


def build_timecourse_pk_dataframe(timecourses: list[dict]) -> pd.DataFrame:
    """
    Convert pre-assembled timecourse records to tidy format.
    Each timecourse record may have 'times' and 'concentrations' arrays.
    """
    rows = []
    for tc in timecourses:
        substance = tc.get("substance") or ""
        if not substance:
            continue
        times = tc.get("times") or []
        concentrations = tc.get("concentrations") or tc.get("values") or []
        study = tc.get("study_sid", "")

        for t, c in zip(times, concentrations):
            try:
                t_f = float(t)
                c_f = float(c)
            except (ValueError, TypeError):
                continue
            if t_f < 0 or c_f < 0:
                continue
            rows.append({
                "study_sid": study,
                "pkdb_sid": substance,
                "substance_label": tc.get("substance_label", substance),
                "time_hr": t_f,
                "conc": c_f,
                "conc_unit": tc.get("unit", ""),
                "time_unit": tc.get("time_unit", "hr"),
                "measurement_type": "concentration",
                "group_pk": tc.get("group_pk"),
                "individual_pk": tc.get("individual_pk"),
                "source": "timecourses",
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        log.info("  Timecourse records: %d rows, %d unique substances",
                 len(df), df["pkdb_sid"].nunique())
    return df


# ---------------------------------------------------------------------------
# Build drug–target dataframe
# ---------------------------------------------------------------------------

def build_target_dataframe(
    mechanisms: list[dict],
    activities: list[dict],
    targets: list[dict],
    mapping: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a drug–target edge list for the bipartite graph.

    Combines mechanism (curated, high-confidence) and activity data.
    Adds target protein metadata (UniProt AC, gene name) from targets.
    """
    # Build target lookup
    target_lookup: dict[str, dict] = {}
    for t in targets:
        tid = t.get("target_chembl_id", "")
        components = t.get("target_components") or []
        uniprot_acs = [
            c.get("accession", "") for c in components
            if c.get("accession")
        ]
        gene_symbols = [
            c.get("component_description", "") for c in components
        ]
        target_lookup[tid] = {
            "target_name": t.get("pref_name", ""),
            "target_type": t.get("target_type", ""),
            "organism": t.get("organism", ""),
            "uniprot_acs": "|".join(uniprot_acs),
            "gene_symbols": "|".join(gene_symbols),
        }

    # Mechanism rows
    mech_rows = []
    for m in mechanisms:
        cid = m.get("molecule_chembl_id", "")
        tid = m.get("target_chembl_id", "")
        if not cid or not tid:
            continue
        t_meta = target_lookup.get(tid, {})
        mech_rows.append({
            "chembl_id": cid,
            "target_chembl_id": tid,
            "interaction_type": "mechanism",
            "action_type": m.get("action_type", ""),
            "mechanism_of_action": m.get("mechanism_of_action", ""),
            "confidence": "curated",
            **t_meta,
        })
    mech_df = pd.DataFrame(mech_rows)

    # Activity rows (supplement mechanisms)
    act_rows = []
    for a in activities:
        cid = a.get("molecule_chembl_id", "")
        tid = a.get("target_chembl_id", "")
        if not cid or not tid:
            continue
        pchembl = a.get("pchembl_value")
        t_meta = target_lookup.get(tid, {})
        act_rows.append({
            "chembl_id": cid,
            "target_chembl_id": tid,
            "interaction_type": "activity",
            "action_type": a.get("standard_type", ""),
            "mechanism_of_action": "",
            "confidence": f"pchembl={pchembl}" if pchembl else "assay",
            **t_meta,
        })
    act_df = pd.DataFrame(act_rows)

    drug_target_df = pd.concat([mech_df, act_df], ignore_index=True)
    if drug_target_df.empty:
        log.warning("No drug-target records found.")
        return drug_target_df

    # Join with mapping to get pkdb_sid
    mapped = mapping[mapping["chembl_id"].notna()][["pkdb_sid", "pkdb_label", "chembl_id"]].drop_duplicates()
    drug_target_df = drug_target_df.merge(mapped, on="chembl_id", how="left")

    log.info("  Drug-target records: %d rows, %d unique compounds, %d unique targets",
             len(drug_target_df),
             drug_target_df["chembl_id"].nunique(),
             drug_target_df["target_chembl_id"].nunique())
    return drug_target_df


# ---------------------------------------------------------------------------
# Assemble pilot dataset
# ---------------------------------------------------------------------------

def assemble_pilot(
    pk_df: pd.DataFrame,
    drug_target_df: pd.DataFrame,
    mapping: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Inner join PK data + ChEMBL targets on pkdb_sid.

    A drug is "usable" if it has:
      - >= MIN_PK_TIMEPOINTS concentration timepoints
      - >= 1 ChEMBL target

    Returns:
      pilot_pk      — PK time-series for usable drugs
      pilot_summary — one row per drug with counts
      pilot_targets — drug–target edges for usable drugs
    """
    if pk_df.empty:
        log.error("PK dataframe is empty — cannot assemble pilot dataset.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Count timepoints per (pkdb_sid, study_sid) combination
    pk_counts = (
        pk_df.groupby("pkdb_sid")
        .agg(
            n_timepoints=("time_hr", "count"),
            n_studies=("study_sid", "nunique"),
            time_min=("time_hr", "min"),
            time_max=("time_hr", "max"),
        )
        .reset_index()
    )
    usable_substances = pk_counts[
        pk_counts["n_timepoints"] >= MIN_PK_TIMEPOINTS
    ]["pkdb_sid"].tolist()

    log.info("Substances with >= %d PK timepoints: %d", MIN_PK_TIMEPOINTS, len(usable_substances))

    # Substances with targets
    if drug_target_df.empty or "pkdb_sid" not in drug_target_df.columns:
        substances_with_targets = set()
    else:
        substances_with_targets = set(
            drug_target_df[drug_target_df["pkdb_sid"].notna()]["pkdb_sid"].unique()
        )
    log.info("Substances with ChEMBL targets: %d", len(substances_with_targets))

    # Intersection
    usable_set = set(usable_substances) & substances_with_targets
    log.info("Substances with PK >= %d timepoints AND targets: %d",
             MIN_PK_TIMEPOINTS, len(usable_set))

    # Build pilot PK
    pilot_pk = pk_df[pk_df["pkdb_sid"].isin(usable_set)].copy()
    pilot_pk = pilot_pk.sort_values(["pkdb_sid", "study_sid", "time_hr"])

    # Build pilot targets
    if drug_target_df.empty:
        pilot_targets = pd.DataFrame()
    else:
        pilot_targets = drug_target_df[
            drug_target_df["pkdb_sid"].isin(usable_set)
        ].copy()

    # Build summary
    summary_rows = []
    for sid in sorted(usable_set):
        pk_sub = pilot_pk[pilot_pk["pkdb_sid"] == sid]
        tgt_sub = pilot_targets[pilot_targets["pkdb_sid"] == sid] if not pilot_targets.empty else pd.DataFrame()
        label = pk_sub["substance_label"].iloc[0] if not pk_sub.empty else sid
        chembl_id = mapping[mapping["pkdb_sid"] == sid]["chembl_id"].iloc[0] if len(mapping[mapping["pkdb_sid"] == sid]) > 0 else ""
        summary_rows.append({
            "pkdb_sid": sid,
            "substance_label": label,
            "chembl_id": chembl_id,
            "n_pk_timepoints": len(pk_sub),
            "n_pk_studies": pk_sub["study_sid"].nunique() if not pk_sub.empty else 0,
            "time_range_hr": f"{pk_sub['time_hr'].min():.1f}–{pk_sub['time_hr'].max():.1f}" if not pk_sub.empty else "",
            "n_targets": len(tgt_sub["target_chembl_id"].unique()) if not tgt_sub.empty else 0,
            "n_mechanisms": len(tgt_sub[tgt_sub["interaction_type"] == "mechanism"]) if not tgt_sub.empty else 0,
            "target_names": "; ".join(tgt_sub["target_name"].dropna().unique()[:3]) if not tgt_sub.empty else "",
        })

    pilot_summary = pd.DataFrame(summary_rows)
    return pilot_pk, pilot_summary, pilot_targets


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def plot_pk_coverage(pk_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    """Plot number of PK timepoints per drug."""
    FIGURES.mkdir(parents=True, exist_ok=True)

    if summary_df.empty:
        log.warning("No data for PK coverage plot.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Phase 1 — PK Data Coverage", fontsize=13, fontweight="bold")

    # Left: timepoints per drug
    ax = axes[0]
    data = summary_df.sort_values("n_pk_timepoints", ascending=False)
    ax.bar(range(len(data)), data["n_pk_timepoints"], color="#2D7DD2")
    ax.set_xlabel("Drug (sorted by timepoints)")
    ax.set_ylabel("Number of PK timepoints")
    ax.set_title(f"PK Timepoints per Drug (n={len(data)})")
    ax.axhline(y=4, color="red", linestyle="--", label="Min threshold (4)")
    ax.legend()

    # Right: target count distribution
    ax2 = axes[1]
    if "n_targets" in summary_df.columns and summary_df["n_targets"].sum() > 0:
        ax2.hist(summary_df["n_targets"], bins=max(1, int(summary_df["n_targets"].max())),
                 color="#97CC04", edgecolor="white")
        ax2.set_xlabel("Number of ChEMBL targets")
        ax2.set_ylabel("Number of drugs")
        ax2.set_title("Target Count Distribution")
    else:
        ax2.text(0.5, 0.5, "No target data", ha="center", va="center", transform=ax2.transAxes)

    plt.tight_layout()
    out = FIGURES / "pk_coverage.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("  Figure saved → %s", out)


def plot_example_trajectories(pilot_pk: pd.DataFrame, n: int = 6) -> None:
    """Plot example PK concentration–time trajectories."""
    if pilot_pk.empty:
        log.warning("No pilot PK data for trajectory plot.")
        return

    drugs = pilot_pk["pkdb_sid"].unique()[:n]
    fig, axes = plt.subplots(2, max(1, (len(drugs) + 1) // 2), figsize=(14, 7))
    axes = axes.flatten() if len(drugs) > 1 else [axes]
    fig.suptitle("Phase 1 — Example PK Trajectories", fontsize=13, fontweight="bold")

    colors = plt.cm.tab10.colors  # type: ignore
    for i, drug in enumerate(drugs):
        ax = axes[i]
        sub = pilot_pk[pilot_pk["pkdb_sid"] == drug].sort_values("time_hr")
        label = sub["substance_label"].iloc[0] if len(sub) else drug
        for j, (study, grp) in enumerate(sub.groupby("study_sid")):
            grp_s = grp.sort_values("time_hr")
            ax.plot(grp_s["time_hr"], grp_s["conc"], "o-",
                    color=colors[j % len(colors)], alpha=0.7,
                    markersize=4, label=study[:12])
        ax.set_title(label[:22], fontsize=9)
        ax.set_xlabel("Time (hr)")
        ax.set_ylabel("Conc.")
        if sub["study_sid"].nunique() <= 3:
            ax.legend(fontsize=6)

    for i in range(len(drugs), len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()
    out = FIGURES / "example_trajectories.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("  Figure saved → %s", out)


# ---------------------------------------------------------------------------
# Feasibility summary table
# ---------------------------------------------------------------------------

def build_feasibility_table(
    mapping: pd.DataFrame,
    pk_df: pd.DataFrame,
    drug_target_df: pd.DataFrame,
    pilot_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Build a summary table for DATA_FEASIBILITY.md."""
    total_substances = len(mapping)
    mapped_chembl = mapping["chembl_id"].notna().sum()
    substances_with_pk = pk_df["pkdb_sid"].nunique() if not pk_df.empty else 0
    substances_with_targets = (
        drug_target_df["pkdb_sid"].nunique()
        if not drug_target_df.empty and "pkdb_sid" in drug_target_df.columns
        else 0
    )
    usable = len(pilot_summary)

    rows = [
        ("Total PK-DB substances (with chemical identity)", total_substances),
        ("Mapped to ChEMBL ID", mapped_chembl),
        ("With PK concentration data (any timepoints)", substances_with_pk),
        (f"With PK data >= {MIN_PK_TIMEPOINTS} timepoints", len([s for s in mapping["pkdb_sid"] if not pk_df.empty and len(pk_df[pk_df["pkdb_sid"] == s]) >= MIN_PK_TIMEPOINTS]) if not pk_df.empty else 0),
        ("With ChEMBL target information", substances_with_targets),
        ("Pilot dataset: drugs with PK + targets", usable),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Count"])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Assemble matched pilot dataset"
    )
    parser.add_argument(
        "--min-timepoints",
        type=int,
        default=MIN_PK_TIMEPOINTS,
        help=f"Minimum PK timepoints for a usable drug (default: {MIN_PK_TIMEPOINTS})",
    )
    args = parser.parse_args()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)

    log.info("=" * 60)
    log.info("Pilot Dataset Builder — Phase 1")
    log.info("=" * 60)

    # Load raw data
    data = load_all_data()
    mapping = load_mapping()

    # Build PK dataframe (outputs + timecourses)
    pk_from_outputs = build_pk_dataframe(data["outputs"])
    pk_from_tcs = build_timecourse_pk_dataframe(data["timecourses"])
    pk_df = pd.concat([pk_from_outputs, pk_from_tcs], ignore_index=True).drop_duplicates()

    if pk_df.empty:
        log.warning("PK dataframe is empty. Check that fetch_pkdb.py ran successfully.")
    else:
        log.info("Combined PK records: %d rows, %d unique substances",
                 len(pk_df), pk_df["pkdb_sid"].nunique())

    # Build drug-target dataframe
    drug_target_df = build_target_dataframe(
        data["mechanisms"],
        data["activities"],
        data["targets"],
        mapping,
    )

    # Assemble pilot
    pilot_pk, pilot_summary, pilot_targets = assemble_pilot(pk_df, drug_target_df, mapping)

    # Save outputs
    if not pilot_pk.empty:
        out = PROCESSED / "pilot_matched.csv"
        pilot_pk.to_csv(out, index=False)
        log.info("Pilot PK saved → %s (%d rows)", out, len(pilot_pk))

    if not pilot_summary.empty:
        out = PROCESSED / "pilot_summary.csv"
        pilot_summary.to_csv(out, index=False)
        log.info("Pilot summary saved → %s (%d drugs)", out, len(pilot_summary))

    if not pilot_targets.empty:
        out = PROCESSED / "pilot_targets.csv"
        pilot_targets.to_csv(out, index=False)
        log.info("Pilot targets saved → %s (%d edges)", out, len(pilot_targets))

    # Feasibility table
    feasibility = build_feasibility_table(mapping, pk_df, drug_target_df, pilot_summary)
    feas_path = TABLES / "feasibility_summary.csv"
    feasibility.to_csv(feas_path, index=False)
    log.info("Feasibility table saved → %s", feas_path)

    # Figures
    plot_pk_coverage(pk_df, pilot_summary)
    plot_example_trajectories(pilot_pk)

    log.info("")
    log.info("=" * 60)
    log.info("Phase 1 Pilot Dataset Summary")
    log.info("=" * 60)
    for _, row in feasibility.iterrows():
        log.info("  %-52s %d", row["Metric"], row["Count"])
    log.info("=" * 60)


if __name__ == "__main__":
    main()
