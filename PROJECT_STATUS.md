# PROJECT STATUS REPORT — Drug-Target Interaction Networks

**Project:** Time-Series Pharmacokinetic Trajectory Clustering on Bipartite Drug-Protein Graphs  
**Date:** 2026-08-24  
**Current Phase:** Transitioning from Phase 3B (Validation Audit) to Phase 4 (Replacement Dataset Acquisition & Validation Gate)  

---

## 1. What Has Been Completed

### 1.1 Phase 1 — Data Collection, Infrastructure & ChEMBL Target Mapping
- **ChEMBL Identifier Mapping Pipeline:** Implemented in [`src/map_identifiers.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/map_identifiers.py). Out of 50 candidate drugs, **46 drugs were successfully mapped to ChEMBL IDs (92% mapping rate)** with **398 associated target proteins**, mechanisms of action, and bioactivities saved in [`data/raw/chembl/`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/data/raw/chembl/).
- **API Harvester:** [`src/fetch_pkdb.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/fetch_pkdb.py) and [`src/fetch_chembl.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/fetch_chembl.py) created with automated pagination, retry backoff, and local caching.
- **Pilot Dataset Assembler:** [`src/build_pilot.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/build_pilot.py) built to link mapped ChEMBL drugs with substance catalog records.
- **Validation Suite:** [`src/validate.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/validate.py) and [`tests/`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/tests/) active with **32 passing unit tests**.

### 1.2 Phase 2 & 3A — Preprocessing Engine & Unit Audits
- **Unit Standardization Module:** [`src/preprocess_pk.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/preprocess_pk.py) created to standardize time to hours (`hr`) and units (`g`, `mg/L`, `becquerel`, etc.).
- **Decision Flowchart Audit:** [`src/apply_decision_flowchart.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/apply_decision_flowchart.py) categorized candidate drugs into readiness tiers.
- **Unit Audit Classifier:** [`src/create_unit_audit_and_conc_only.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/create_unit_audit_and_conc_only.py) generated [`pk_unit_audit.csv`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/data/processed/pk_unit_audit.csv).

### 1.3 Phase 3B — Raw Concentration Audit & Scientific Validation Gate
- **Trace Audit Execution:** Created [`src/generate_concentration_recovery_audit.py`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/src/generate_concentration_recovery_audit.py) to trace all 942 records across the 9 Category-A drugs from raw PK-DB API ZIP archives (`interventions.csv`, `scatters.csv`, `outputs.csv`, `timecourses.csv`).
- **Audit Findings Artifacts:** Produced [`pk_concentration_recovery_audit.csv`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/data/processed/pk_concentration_recovery_audit.csv), [`pk_concentration_recovery_summary.csv`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/data/processed/pk_concentration_recovery_summary.csv), and [`PHASE_3B_STATUS.md`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/PHASE_3B_STATUS.md).
- **Proved Payload Restriction:** Verified that `timecourses.csv` in raw ZIP downloads from PK-DB's unauthenticated REST API `/api/v1/filter/?download=true` contains **0 rows**. All 942 extracted records were administered dosing events (`g`, `g/kg`, `becquerel`, `ml`) or bivariate scatter plot points (AUC vs. Conc at isolated timepoints 192/576h).

---

## 2. What Has Been Partially Completed

- **Pharmacokinetic Trajectory Pipeline:** Data extraction and unit standardization architecture built, but currently operating on empty/non-concentration observations.
- **Matched Drug-Target Matrix:** ChEMBL drug-target network side is 100% ready; PK trajectory side awaits open $C(t)$ data.

---

## 3. What Is Currently Blocked

- **Pharmacokinetic Feature Engineering ($C_{\max}, T_{\max}, AUC, k_e$):** BLOCKED (0 valid plasma concentration time-series).
- **Singular Value Decomposition (SVD):** BLOCKED (cannot construct drug-by-time matrix).
- **Dynamic Mode Decomposition (DMD):** BLOCKED (0 continuous state trajectories).
- **Trajectory Clustering (DTW / k-means):** BLOCKED.
- **Bipartite Drug-Protein Trajectory Graph Analysis:** BLOCKED on PK side.

---

## 4. Why Current PK-DB Data Cannot Support Trajectory Modeling

1. **Zero $C(t)$ Observations:** 100% of extracted observations from PK-DB unauthenticated API zip files represent administered drug doses (e.g. 100 mg oral dose at $t=0$) or bivariate scatter plot ratio points, NOT plasma concentration measurements over time.
2. **Rejected Pseudo-Concentration Data:** The 44 records for `losartan` and `exp3174` previously retained by naive unit matching (`mole / liter`) were bivariate scatter comparison points at isolated timepoints (192 hr & 576 hr). They are **REJECTED** and must not be used for modeling.
3. **Scientific Impossibility:** A model cannot estimate clearance, half-life, $C_{\max}$, AUC, or state transition operators (DMD) from administered dose values or isolated scatter points.

---

## 5. Status of Original Research Objectives

| Original Research Objective | Status | Impact / Next Action |
|---|---|---|
| ChEMBL Drug-Protein Bipartite Graph Construction | **ACHIEVABLE (100% Ready)** | 46 mapped drugs, 398 target proteins ready |
| Cross-Database Identifier Mapping Framework | **ACHIEVABLE (100% Ready)** | Multi-tier mapping logic validated |
| Time-Series Concentration Trajectory Ingestion | **BLOCKED on PK-DB API** | Requires open-access replacement dataset |
| Trajectory Feature Extraction ($C_{\max}, AUC, k_e$) | **PAUSED** | Awaits Phase 4 replacement dataset |
| Trajectory Clustering on Bipartite Graphs | **PAUSED** | Awaits Phase 4 validation gate |

---

## 6. Exact Next Phase Required

**PHASE 4 — OPEN PK CONCENTRATION DATASET ACQUISITION, STANDARDIZATION & VALIDATION GATE**

---
