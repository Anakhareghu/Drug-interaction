# PHASE 5A STATUS — Modeling Matrix Preparation & Preprocessing Report

**Project:** Drug-Target Interaction Networks: Time-Series Pharmacokinetic Trajectory Clustering on Bipartite Drug-Protein Graphs  
**Phase:** Phase 5A — Modeling Matrix Preparation and Preprocessing  
**Date:** 2026-08-25  
**Status:** COMPLETE & SCIENTIFICALLY VALIDATED (`READY_FOR_SVD_DMD = TRUE`)  

---

## 1. Executive Summary

Phase 5A converts the validated 5,174 subject-level plasma/serum concentration measurements into dense, standardized **$7 \times 15$ drug-level trajectory matrices** (`data/processed/pk_phase5_dose_normalized_matrix.csv` and `data/processed/pk_phase5_peak_normalized_matrix.csv`).

No numerical modeling algorithms (SVD, DMD, trajectory clustering, AUC, $C_{\max}$, $T_{\max}$, $k_e$ estimation, curve fitting, or bipartite graph clustering) were executed during this phase.

---

## 2. Pipeline Execution Stages & Findings

### Stage 1: Input Validation
- Loaded **[`data/processed/pk_phase4_extended_clean.csv`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/data/processed/pk_phase4_extended_clean.csv)**.
- Verified 100% of retained records (5,174 rows across 7 validated drugs) are measured $C(t) > 0$ plasma/serum concentrations with non-negative timestamps (`time_hr`), valid subject/study IDs, and explicit dose values (`dose_mg`).

### Stage 2: Subject-Level Trajectory Construction
- Constructed subject-level curves for all 452 unique subjects across 7 drugs.
- Sorted by timestamp and averaged duplicate measurements at identical time points per subject.

### Stage 3: Baseline ($t=0$) Handling
- Retained measured baseline concentrations where present (e.g. 3 subjects in Theophylline with pre-dose baseline). For oral drugs lacking pre-dose measurements, $C(0) = 0$ was enforced physically without fabricating non-zero concentrations.

### Stage 4 & 5: Dose & Peak Normalization
- Calculated **Dose-Normalized Concentration:** $C_{\text{norm}}(t) = C(t) / \text{Dose\_mg}$ (rescales trajectories to unit dose exposure).
- Calculated **Peak-Normalized Concentration:** $C_{\text{peak\_norm}}(t) = C(t) / C_{\max,\text{subject}}$ (isolates kinetic curve morphology from exposure scale).

### Stage 6: Standard Time Grid & Interpolation
- Evaluated all subject curves on a standard 15-point temporal evaluation grid:  
  `T_GRID = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0, 24.0] hr`
- Used **Pchip (Piecewise Cubic Hermite Interpolating Polynomial)** monotonic interpolation to eliminate non-physical polynomial oscillations.
- Short-acting drugs (Remifentanil $< 4\text{ h}$, Cefamandole $< 6\text{ h}$) reaching complete clearance had terminal post-elimination grid points set to $0.0$ physically.

### Stage 7: Subject $\to$ Drug Aggregation
- Computed drug-level `mean`, `median`, `std`, `n_subjects`, and `standard_error` across eligible subjects for each drug and timepoint (105 aggregated rows).
- Ensured equal weighting per drug in the final matrix to prevent high-subject drugs (e.g. Xanomeline $N=168$) from dominating.

### Stage 8: Candidate Matrix Validation
- Exported candidate $7 \times 15$ matrices to **[`data/processed/pk_phase5_dose_normalized_matrix.csv`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/data/processed/pk_phase5_dose_normalized_matrix.csv)** and **[`data/processed/pk_phase5_peak_normalized_matrix.csv`](file:///c:/Users/ANAKHA/OneDrive/Desktop/DRUG%20INTERACTION/data/processed/pk_phase5_peak_normalized_matrix.csv)**.
- Verified dimensions ($7 \times 15$), **0 NaNs**, **0 Infs**, **100% finite values**, 0 duplicate rows/columns.

---

## 3. Generated Artifacts & Summary Files

1. **`data/processed/pk_phase5_subject_trajectories.csv`**: 6,780 subject-grid rows (452 subjects $\times$ 15 timepoints).
2. **`data/processed/pk_phase5_drug_mean_trajectories.csv`**: 105 drug-grid rows (7 drugs $\times$ 15 timepoints).
3. **`data/processed/pk_phase5_dose_normalized_matrix.csv`**: $7 \times 15$ dose-normalized matrix.
4. **`data/processed/pk_phase5_peak_normalized_matrix.csv`**: $7 \times 15$ peak-normalized matrix.
5. **`data/processed/pk_phase5_trajectory_statistics.csv`**: Uncertainty audit statistics.
6. **`data/processed/pk_phase5_preprocessing_audit.csv`**: Stage-by-stage transformation audit log.
7. **`tests/test_phase5a_modeling_matrix.py`**: Automated test suite (44 total unit tests passing).

---

## 4. Responses to Critical Scientific Checks

1. **Subject Stability:** All 7 drugs have adequate subject counts ($N=6$ to $N=168$) for stable mean trajectories.
2. **Temporal Coverage:** Grid covers 0 to 24h. Ultra-short-acting IV drugs reach zero concentration past 4–6h; long-elimination drugs (Phenobarbital, Quinidine) are evaluated during their initial 24h phase.
3. **Interpolation vs. Extrapolation:** Pchip interpolation is bounded within observed subject time windows; post-clearance terminal points for ultra-short IV drugs reach zero. 0 extrapolation required.
4. **Dose Consistency:** Dose values are 100% consistent per subject/study.
5. **Dose & Peak Normalization:** Peak normalization successfully bounds values to $[0.0, 1.0]$. Dose normalization ranges cleanly without extreme outliers.
6. **Matrix & Route Heterogeneity:** IV bolus, IV infusion, and Oral routes are preserved and annotated as kinetic curve descriptors.

---

## 5. Final Required Scientific Status Summary

```
CURRENT PHASE: PHASE 5A — MODELING MATRIX PREPARATION
INPUT DATASET: data/processed/pk_phase4_extended_clean.csv
VALIDATED DRUGS: 7 (cefamandole, indomethacin, phenobarbital, quinidine, remifentanil, theophylline, xanomeline)
SUBJECT COUNT: 452
SUBJECT-LEVEL TRAJECTORIES: 6,780 rows (452 subjects × 15 timepoints)
DRUG-LEVEL TRAJECTORIES: 105 rows (7 drugs × 15 timepoints)
TIME GRID: [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0, 24.0] hr (15 points)
DOSE NORMALIZATION STATUS: COMPLETE (C_norm = C / Dose_mg; 0 NaNs, 0 Infs)
PEAK NORMALIZATION STATUS: COMPLETE (C_peak = C / Cmax; 0 NaNs, 0 Infs, max <= 1.0)
INTERPOLATION METHOD: Pchip Monotonic Cubic Interpolation
EXTRAPOLATION REQUIRED: NONE (Terminal clearance post-elimination for remifentanil/cefamandole explicitly zeroed at terminal points; no high-order polynomial oscillations)
FINAL MATRIX DIMENSIONS: 7 × 15
MISSING VALUES: 0 (0 NaNs, 0 Infs across both candidate matrices)
MAJOR SCIENTIFIC RISKS: Route differences (IV vs. Oral) create distinct kinetic shapes; long-elimination drugs (Phenobarbital, Quinidine) sampled >24h are evaluated during initial 0-24h window.
READY_FOR_SVD_DMD: TRUE
NEXT EXACT STEP: Phase 5B — Perform Singular Value Decomposition (SVD) & Dynamic Mode Decomposition (DMD) matrix factorisations on the candidate matrices.
```
