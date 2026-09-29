# Phase 4 Implementation Plan — Replacement Open PK Dataset Acquisition & Validation Gate

## Goal
Acquire, standardize, and validate an open-access replacement Pharmacokinetic (PK) concentration-vs-time dataset ($C(t)$ in plasma/serum) to replace the unauthenticated PK-DB API data. Establish a strict Phase 4 Validation Gate before proceeding to any downstream numerical PK modeling, SVD, DMD, or trajectory clustering.

---

## User Review Required

> [!IMPORTANT]
> **Dataset Selection Recommendation:** We recommend **Candidate 1: Pharmacometrics Benchmark PK Corpus (`PKNCA` / `nlme` / `mrgsolve` / Open PK Benchmark)** combined with **Candidate 2 (Zenodo / OSF Open PK-DB Study Dumps)** as the replacement dataset.  
> - 100% open-license (GPL / CC-BY 4.0).
> - Provides dense plasma concentration time-series ($C_{\text{plasma}}(t)$) for 10–20 small-molecule drugs with subject IDs, exact timepoints (hr), dosing (mg), and plasma matrix metadata.
> - All candidate drugs map 1:1 to ChEMBL target networks.

---

## Proposed Data Distinction Framework

To preserve pipeline integrity and prevent data corruption, all datasets in the repository will be strictly partitioned:

1. **VALIDATED DATA (`data/processed/chembl_*`, `data/processed/id_mapping_table.csv`):**  
   ChEMBL drug-target interaction networks, protein targets, and identifier cross-mappings (100% validated).
2. **REJECTED DATA (`data/processed/pk_timecourses_clean.csv`, `pk_phase3_input.csv`, `pk_phase3_concentration_only.csv`):**  
   PK-DB unauthenticated API records (dosing interventions, scatter ratio points). Preserved unchanged for auditing; flagged as `REJECTED_FOR_MODELING`.
3. **CANDIDATE REPLACEMENT DATA (`data/raw/replacement_pk/`, `data/processed/pk_phase4_clean.csv`):**  
   New longitudinal plasma concentration-time observations fetched in Phase 4.

---

## Proposed Code Changes

### Component 1: Data Acquisition & Preprocessing Engine

#### [NEW] [src/fetch_replacement_pk.py](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/fetch_replacement_pk.py)
Downloads and extracts raw longitudinal plasma concentration-time datasets from Candidate 1 & 2 open repositories into `data/raw/replacement_pk/`.

#### [NEW] [src/preprocess_replacement_pk.py](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/preprocess_replacement_pk.py)
Parses replacement PK data, standardizes time to hours (`hr`), converts concentrations to standard units (`mg/L` or `ug/L`), validates biological matrix (`plasma`/`serum`), and exports `data/processed/pk_phase4_clean.csv`.

#### [NEW] [src/validate_phase4_gate.py](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/validate_phase4_gate.py)
Executes strict validation checks on `data/processed/pk_phase4_clean.csv` to enforce the Phase 4 Validation Gate criteria.

---

### Component 2: Preserved Existing Modules (NO CHANGES)

- [`src/fetch_chembl.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/fetch_chembl.py) — Preserved unchanged.
- [`src/map_identifiers.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/map_identifiers.py) — Preserved unchanged.
- [`src/build_pilot.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/build_pilot.py) — Preserved unchanged.
- [`src/validate.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/validate.py) — Preserved unchanged.
- [`src/generate_concentration_recovery_audit.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/generate_concentration_recovery_audit.py) — Preserved unchanged as Phase 3B audit record.

---

## Target Schema for Phase 4 Replacement Dataset (`pk_phase4_clean.csv`)

| Column Name | Type | Description | Example |
|---|---|---|---|
| `drug_name` | String | Common drug name | `theophylline` |
| `chembl_id` | String | Valid ChEMBL accession | `CHEMBL178` |
| `study_id` | String | Study / Trial identifier | `STUDY_THEO_01` |
| `subject_id` | String | Unique subject identifier | `SUBJ_01` |
| `time_hr` | Float | Measurement time in hours | `2.0` |
| `concentration` | Float | Measured drug concentration | `7.05` |
| `concentration_unit` | String | Standardized unit | `mg/L` |
| `biological_matrix` | String | Tissue/fluid sampled | `plasma` |
| `route` | String | Administration route | `oral` |
| `dose_mg` | Float | Administered dose mass | `320.0` |
| `is_plasma_concentration` | Boolean | Hard verification flag | `True` |

---

## Phase 4 Validation Gate Criteria

The replacement dataset will be declared **`READY_FOR_PK_MODELING`** ONLY IF ALL of the following criteria pass:

1. **ChEMBL Linkage:** $\ge 10$ unique drugs mapped 1:1 to ChEMBL IDs with associated target proteins.
2. **Biological Matrix Verification:** 100% of observations verified as measured drug concentration in plasma or serum (`is_plasma_concentration == True`).
3. **Observation Type:** 0 dosing interventions (`gram`, `becquerel`), 0 volume measurements (`ml`), 0 scatter plot ratio points.
4. **Sampling Granularity:** Each drug must possess $\ge 5$ distinct post-dose time points ($t > 0\text{ hr}$) forming a trajectory curve.
5. **Feature Calculability:** Dataset enables mathematical estimation of $C_{\max}$, $T_{\max}$, $AUC_{0-\infty}$, and elimination rate constant ($k_e$).
6. **Matrix Construction:** Time grid permits constructing a non-empty 2D drug-by-time feature matrix for SVD and DMD.

---

## Verification Plan

### Automated Tests
- Run updated test suite:
  `python -m pytest tests/ -v`
- Run Phase 4 Validation Gate script:
  `python src/validate_phase4_gate.py`

### Expected Output Files
- `data/processed/pk_phase4_clean.csv`
- `data/processed/pk_phase4_summary.csv`
- `data/processed/pk_phase4_gate_report.json`
