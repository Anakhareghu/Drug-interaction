# Drug-Target Interaction Networks
## Time-Series Pharmacokinetic Trajectory Clustering on Bipartite Drug-Protein Graphs
### Project P23 — Phase 1: Data Collection & Feasibility

---

## Overview

This project investigates whether pharmacokinetic (PK) concentration–time trajectories can be used to cluster drugs by their biological target interactions, using a bipartite drug–protein graph framework.

**Phase 1** focuses entirely on data collection and feasibility assessment — building a reliable, small pilot dataset that links:
- **PK time-series** (concentration vs. time) from [PK-DB](https://pk-db.com)
- **Drug–target interactions** (compound ↔ protein) from [ChEMBL](https://www.ebi.ac.uk/chembl/)

---

## Project Structure

```
DRUG INTERACTION/
├── data/
│   ├── raw/
│   │   ├── pkdb/               # Raw PK-DB API responses (JSON, preserved unchanged)
│   │   └── chembl/             # Raw ChEMBL API responses (JSON, preserved unchanged)
│   └── processed/              # Matched, cleaned pilot dataset (CSV + JSON)
├── notebooks/                  # Exploratory notebooks (Phase 1 EDA)
├── src/                        # Core Python source modules
│   ├── fetch_pkdb.py           # PK-DB data fetcher
│   ├── fetch_chembl.py         # ChEMBL data fetcher
│   ├── map_identifiers.py      # Cross-database ID mapping
│   ├── build_pilot.py          # Assemble matched pilot dataset
│   └── validate.py             # Data validation
├── outputs/
│   ├── figures/                # Feasibility plots
│   └── tables/                 # Summary tables
├── tests/                      # Unit tests for Phase 1 modules
├── README.md
├── requirements.txt
├── DATA_FEASIBILITY.md         # Phase 1 findings report
└── .gitignore
```

---

## Phase 1 Scope

| ✅ In Scope (Phase 1)                           | ❌ Out of Scope (Future Phases) |
|-------------------------------------------------|---------------------------------|
| PK-DB API download (pilot 20–50 drugs)          | SVD / matrix factorisation      |
| ChEMBL API download (drug–target pairs)         | Trajectory clustering (DTW etc) |
| Identifier mapping (ChEMBL IDs, InChIKey, CHEBI)| DMD / Koopman operator analysis |
| Processed matched dataset                       | Full pipeline orchestration     |
| Data validation & feasibility report            | Graph neural networks           |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Fetch PK-DB data

```bash
python src/fetch_pkdb.py
```

Downloads:
- `data/raw/pkdb/substances.json`  — all PK-DB substance nodes with cross-refs
- `data/raw/pkdb/timecourses.json` — PK time-series (concentration + time)
- `data/raw/pkdb/interventions.json` — dosing metadata

### 3. Fetch ChEMBL data

```bash
python src/fetch_chembl.py
```

Downloads:
- `data/raw/chembl/drug_targets.json` — ChEMBL activity/mechanism data

### 4. Map identifiers & build pilot dataset

```bash
python src/map_identifiers.py
python src/build_pilot.py
```

Produces:
- `data/processed/pilot_matched.csv`
- `data/processed/id_mapping_table.csv`
- `outputs/tables/feasibility_summary.csv`

### 5. Run validation

```bash
python src/validate.py
```

### 6. Run tests

```bash
pytest tests/ -v
```

---

## Identifier Mapping Strategy

The bridge between PK-DB and ChEMBL is established using **ChEMBL IDs embedded in PK-DB substance records**:

1. Fetch all PK-DB substance `info_nodes` (`ntype=substance`)
2. Extract `xrefs` where `name == "chembl"` → gives `CHEMBLXXX` accession directly
3. For substances lacking a direct ChEMBL xref, fall back to:
   - InChIKey lookup via ChEMBL molecule search
   - CHEBI ID lookup
4. Name-based fuzzy matching is **not used** as primary strategy

This yields a reliable, programmatic mapping without ambiguous drug-name matching.

---

## Data Sources

| Source | Access | License |
|--------|--------|---------|
| [PK-DB](https://pk-db.com) | REST API (`https://pk-db.com/api/v1/`) | CC-BY 4.0 |
| [ChEMBL](https://www.ebi.ac.uk/chembl/) | REST API + `chembl_webresource_client` | CC-BY-SA 3.0 |

---

## Phase 1 Deliverables

- [ ] Directory scaffold with all required folders
- [ ] Raw PK-DB data preserved in `data/raw/pkdb/`
- [ ] Raw ChEMBL data preserved in `data/raw/chembl/`
- [ ] `data/processed/pilot_matched.csv` — drugs with PK + targets
- [ ] `DATA_FEASIBILITY.md` — full report
- [ ] Unit tests in `tests/`

---

## Citation

If you use this data pipeline, please cite the underlying databases:

- **PK-DB**: Grzegorzewski et al. (2022). *PK-DB: pharmacokinetics database for individualized and stratified computational modeling.* Nucleic Acids Research. https://doi.org/10.1093/nar/gkab1028
- **ChEMBL**: Mendez et al. (2019). *ChEMBL: towards direct deposition of bioassay data.* Nucleic Acids Research. https://doi.org/10.1093/nar/gky1075
