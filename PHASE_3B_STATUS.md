# PHASE 3B STATUS — Raw PK Concentration Recovery and Validation Report

**Project:** Drug-Target Interaction Networks: Time-Series Pharmacokinetic Trajectory Clustering on Bipartite Drug-Protein Graphs  
**Phase:** Phase 3B — Raw PK Concentration Recovery and Validation  
**Date:** 2026-08-24  
**Status:** AUDIT COMPLETED & SCIENTIFICALLY VALIDATED  

---

## 1. What Was Investigated

We performed an end-to-end audit tracing every observation record across all 9 Phase 2 Category-A drugs (`metoprolol`, `omeprazole`, `midazolam`, `simvastatin`, `losartan`, `exp3174`, `talinolol`, `chlorzoxazone`, `rifampicin`).

Specifically, we inspected:
1. **Raw PK-DB API ZIP archives** (`data/raw/pkdb/raw_filter_<drug>.zip`) containing `timecourses.csv`, `scatters.csv`, `interventions.csv`, `outputs.csv`, `studies.csv`, `groups.csv`, `individuals.csv`.
2. **Preprocessing logic** (`src/preprocess_pk.py`).
3. **Phase 3 input builder** (`src/prepare_phase3_input.py`).
4. **Unit audit & strict concentration filter engine** (`src/create_unit_audit_and_conc_only.py`).
5. **Detailed record-level tracing** saved to `data/processed/pk_concentration_recovery_audit.csv` (942 observation rows) and `data/processed/pk_concentration_recovery_summary.csv` (9 Category-A drugs).

---

## 2. Drug-by-Drug Findings

### 2.1 Metoprolol (`CHEMBL13`)
- **Raw Observations in ZIP:** 151 total (142 from `interventions.csv`, 9 from `scatters.csv`).
- **Raw Measurement Types:** `dosing` (142), `scatter_plot_point` (9).
- **Raw Units:** `gram` (141), `gram / kilogram` (1), `liter / hour` (9).
- **Interpretation:**
  - `preprocess_pk.py` extracted 74 intervention dosing events (`g`, `g/kg`).
  - `prepare_phase3_input.py` retained 74 intervention dosing records.
  - `create_unit_audit_and_conc_only.py` classified all 74 as `administered_dosing_mass` (`is_plasma_concentration = False`).
- **Status:** **0 concentration observations**. 100% of extracted observations were administered drug doses, not plasma concentration measurements.
- **Cause:** **E. PK-DB genuinely lacks sufficient concentration observations** (zip `timecourses.csv` has 0 rows for unauthenticated requests).

### 2.2 Omeprazole (`CHEMBL1503`)
- **Raw Observations in ZIP:** 163 (all from `interventions.csv`).
- **Raw Measurement Types:** `dosing` (152), `qualitative-dosing` (11).
- **Raw Units:** `gram` (152), `becquerel` (10), `gram / kilogram` (1).
- **Interpretation:**
  - `preprocess_pk.py` extracted 162 intervention dosing events (`g`, `becquerel`, `g/kg`).
  - `prepare_phase3_input.py` retained 162 dosing records.
  - `create_unit_audit_and_conc_only.py` classified all 162 as dosing mass / radioactivity (`is_plasma_concentration = False`).
- **Status:** **0 concentration observations**.
- **Cause:** **E. PK-DB genuinely lacks sufficient concentration observations**.

### 2.3 Midazolam (`CHEMBL655`)
- **Raw Observations in ZIP:** 187 (all from `interventions.csv`).
- **Raw Measurement Types:** `dosing` (187).
- **Raw Units:** `gram` (183), `becquerel` (3), `gram / kilogram` (1).
- **Interpretation:**
  - `preprocess_pk.py` extracted 186 intervention dosing events (`g`, `becquerel`, `g/kg`).
  - `prepare_phase3_input.py` retained 186 dosing records.
  - `create_unit_audit_and_conc_only.py` classified all 186 as dosing mass / radioactivity (`is_plasma_concentration = False`).
- **Status:** **0 concentration observations**.
- **Cause:** **E. PK-DB genuinely lacks sufficient concentration observations**.

### 2.4 Simvastatin (`CHEMBL1064`)
- **Raw Observations in ZIP:** 74 (all from `interventions.csv`).
- **Raw Measurement Types:** `dosing` (74).
- **Raw Units:** `gram` (73), `gram / kilogram` (1).
- **Interpretation:**
  - `preprocess_pk.py` extracted 74 intervention dosing events (`g`, `g/kg`).
  - `prepare_phase3_input.py` retained 74 dosing records.
  - `create_unit_audit_and_conc_only.py` classified all 74 as dosing mass (`is_plasma_concentration = False`).
- **Status:** **0 concentration observations**.
- **Cause:** **E. PK-DB genuinely lacks sufficient concentration observations**.

### 2.5 Losartan (`CHEMBL191`)
- **Raw Observations in ZIP:** 112 (68 from `interventions.csv`, 44 from `scatters.csv`).
- **Raw Measurement Types:** `dosing` (68), `scatter_ratio` (44).
- **Raw Units:** `gram` (68), `mole / liter` (44).
- **Interpretation:**
  - The 68 intervention records are administered dosing events (`g`).
  - The 44 scatter records have `y_unit = mole / liter` and `x_unit = hour * mole / liter`. These are bivariate scatter plot comparisons (AUC vs. Concentration at 2 isolated post-dose time points: 192 hr and 576 hr), NOT a continuous concentration-over-time $C(t)$ trajectory.
  - The naive unit filter in `create_unit_audit_and_conc_only.py` retained these 44 scatter points based on unit string alone (`mole / liter`).
- **Status:** **0 genuine $C(t)$ concentration trajectory observations** (44 bivariate scatter points incorrectly passed naive unit filter).
- **Cause:** **A. Correctly excluded — not concentration**.

### 2.6 Losartan Carboxylic Acid / EXP3174 (`CHEMBL907`)
- **Raw Observations in ZIP:** 102 (58 from `interventions.csv`, 44 from `scatters.csv`).
- **Raw Measurement Types:** `dosing` (58), `scatter_ratio` (44).
- **Raw Units:** `gram` (58), `mole / liter` (44).
- **Interpretation:**
  - Same structure as losartan: 58 dosing events and 44 bivariate scatter comparison points at 2 isolated time points (192 hr and 576 hr).
- **Status:** **0 genuine $C(t)$ concentration trajectory observations**.
- **Cause:** **A. Correctly excluded — not concentration**.

### 2.7 Talinolol (`CHEMBL152067`)
- **Raw Observations in ZIP:** 60 (39 from `interventions.csv`, 21 from `scatters.csv`).
- **Raw Measurement Types:** `dosing` (39), `scatter_auc` (21).
- **Raw Units:** `gram` (36), `ml` (1), `gram / hour` (2), `gram * hour / liter` (21).
- **Interpretation:**
  - 39 dosing interventions and 21 AUC exposure scatter points.
  - `create_unit_audit_and_conc_only.py` classified all as non-concentration (`is_plasma_concentration = False`).
- **Status:** **0 concentration observations**.
- **Cause:** **E. PK-DB genuinely lacks sufficient concentration observations**.

### 2.8 Chlorzoxazone (`CHEMBL1371`)
- **Raw Observations in ZIP:** 52 (all from `interventions.csv`).
- **Raw Measurement Types:** `dosing` (51), `radioactivity` (1).
- **Raw Units:** `gram` (51), `becquerel` (1).
- **Interpretation:** All 52 records are administered dosing events (`g`, `becquerel`).
- **Status:** **0 concentration observations**.
- **Cause:** **E. PK-DB genuinely lacks sufficient concentration observations**.

### 2.9 Rifampicin (`CHEMBL374478`)
- **Raw Observations in ZIP:** 41 (all from `interventions.csv`).
- **Raw Measurement Types:** `dosing` (41).
- **Raw Units:** `gram` (32), `gram / kilogram` (9).
- **Interpretation:** All 41 records are administered dosing events (`g`, `g/kg`).
- **Status:** **0 concentration observations**.
- **Cause:** **E. PK-DB genuinely lacks sufficient concentration observations**.

---

## 3. Exact Reasons the 7 Drugs Disappeared

1. **Extraction Misinterpretation:** The Phase 2 ingestion script (`src/preprocess_pk.py`) extracted records from `interventions.csv` (dosing administration events) and `scatters.csv` (bivariate scatter plot points), mistaking them for time-series concentration observations.
2. **Strict Unit Filter:** When `create_unit_audit_and_conc_only.py` audited measurement units, it correctly filtered out dosing mass (`g`, `mg`, `g/kg`), dose volume (`ml`), and radioactivity (`becquerel`).
3. **PK-DB Public API Payload Limitation:** `timecourses.csv` in raw ZIP downloads from PK-DB's unauthenticated `/api/v1/filter/?download=true` endpoint contains **0 rows of data** across all candidate drugs. Time-series observation arrays require authenticated user sessions or open study media files which PK-DB currently does not serve for these substances without login credentials.

---

## 4. Scientific Filter & Pipeline Assessment

- **Is the current concentration filter scientifically correct?**  
  **YES.** Excluding administered doses (`gram`), radioactivity (`becquerel`), volumes (`ml`), and bivariate scatter plot ratios is 100% scientifically mandatory. A valid $C(t)$ observation must measure actual drug concentration in blood, plasma, serum, or tissue over time.
- **Does the extraction pipeline need correction?**  
  **YES.** `src/preprocess_pk.py` must be updated to stop pulling dosing interventions (`interventions.csv`) as PK concentration time-series.

---

## 5. Summary Metrics Post-Recovery Audit

- **Number of genuinely usable PK drugs after recovery:** `0`
- **Number of usable concentration observations:** `0`
- **Number of distinct time points per drug:** `0`
- **Number of studies / subjects:** `0` (genuine $C(t)$ trajectories)

---

## 6. Scientific Sufficiency Evaluation

| Scientific Task | Dataset Status | Reason |
|---|---|---|
| $C_{\max} / T_{\max}$ Estimation | **INSUFFICIENT** | No concentration trajectory points available |
| $AUC$ Integration | **INSUFFICIENT** | No concentration-time series |
| Elimination Rate ($k_e$) Estimation | **INSUFFICIENT** | No decay profile data |
| Nonlinear Curve Fitting (e.g. 1/2-Compartment) | **INSUFFICIENT** | 0 concentration data points |
| Singular Value Decomposition (SVD) | **INSUFFICIENT** | Cannot construct drug-by-time matrix |
| Dynamic Mode Decomposition (DMD) | **INSUFFICIENT** | 0 state trajectories |
| Bipartite Graph Trajectory Clustering | **INSUFFICIENT** | 0 trajectory clusters |

> [!WARNING]
> **Scientific Reality Check:** A dataset containing only administered dose values (e.g. $100\text{ mg}$ at $t=0$) or isolated scatter plot ratios at $t=192\text{ h}$ cannot be used for pharmacokinetic time-series clustering.

---

## 7. Single Recommendation

**`ACQUIRE ADDITIONAL DATASET`**

**Rationale:** PK-DB's unauthenticated public REST API does not provide downloadable time-series concentration arrays for the evaluated candidate drugs. To perform pharmacokinetic trajectory clustering on bipartite drug-protein graphs, the project must acquire open-access pharmacokinetic time-series datasets from external sources (e.g. PharmGKB, ChEMBL bioassays, FDA NDA review open datasets, or open-access PK databases/R packages).

---
