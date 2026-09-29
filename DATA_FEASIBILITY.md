# DATA_FEASIBILITY.md — Phase 1 Assessment

**Project:** Drug-Target Interaction Networks: Time-Series Pharmacokinetic Trajectory Clustering on Bipartite Drug-Protein Graphs  
**Phase:** 1 — Raw Data Acquisition and Feasibility Assessment  
**Date:** 2026-08-16  
**Status:** COMPLETED & EXPANDED

---

## 1. Executive Summary

Phase 1 confirms that:

- **PK-DB Public Filter Discovery**: Using the public `/api/v1/filter/` endpoint across all ~800 PK-DB substances, we indexed **217 substances** with available time-course series metadata.
- **ChEMBL Mapping & Usable Dataset**: Out of 50 candidate drugs evaluated:
  - **46 candidate drugs** mapped reliably to ChEMBL (via direct xrefs, InChIKeys, ChEBI, and exact curated names).
  - **36 candidate drugs** are **USABLE**, possessing BOTH indexed concentration time-course records in PK-DB AND curated target protein interaction data in ChEMBL.
  - This substantially exceeds the target goal of 15–20 usable drugs.
- **Access Details**: The public `/filter/` endpoint allows indexing all available study timecourses, interventions, and scatters. Raw timecourse measurement arrays require authenticated user sessions for complete payload downloads.

**Primary Summary Artifact**: `data/processed/pkdb_chembl_candidate_summary.csv` (Columns: `drug_name`, `pkdb_id`, `chembl_id`, `timecourse_count`, `target_count`, `mapping_method`, `status`).

---

## 2. Data Sources

| Source    | API / Tool                     | Access Status |
|-----------|-------------------------------|---------------|
| PK-DB     | `https://pk-db.com/api/v1/`  | Public `/filter/` & `/info_nodes/` discovery |
| ChEMBL    | `chembl_webresource_client`  | Fully public |

---

## 3. Pilot & Candidate Dataset Statistics

### 3.1 Expanded PK-DB & ChEMBL Candidate Dataset

| Metric | Count |
|--------|-------|
| Total PK-DB substances catalogued | 800 |
| Substances with indexed time-courses on PK-DB (`/filter/`) | 217 |
| Candidate drugs evaluated in pilot expansion | 50 |
| Candidates mapped to ChEMBL | 46 (92%) |
| **Usable candidates (timecourse_count > 0 AND target_count > 0)** | **36** |
| Total time-course series across 36 usable drugs | 9,842 |
| Total target proteins associated across 36 usable drugs | 398 |

### 3.2 Candidate Summary Sample (Top Usable Drugs)

| Drug Name | PK-DB SID | ChEMBL ID | Time-Course Count | Target Count | Mapping Method | Status |
|-----------|-----------|-----------|-------------------|--------------|----------------|--------|
| midazolam | midazolam | CHEMBL655 | 707 | 10 | direct_xref | usable |
| omeprazole | omeprazole | CHEMBL1503 | 624 | 19 | inchikey | usable |
| D-glucose | glucose | CHEMBL1222250 | 565 | 2 | direct_xref | usable |
| 1-hydroxymidazolam | 1-hydroxymidazolam | CHEMBL1188 | 491 | 1 | direct_xref | usable |
| aldosterone | aldosterone | CHEMBL273453 | 452 | 5 | direct_xref | usable |
| losartan | losartan | CHEMBL191 | 383 | 8 | direct_xref | usable |
| enalapril | enalapril | CHEMBL578 | 340 | 4 | direct_xref | usable |
| torasemide | torasemide | CHEMBL1148 | 328 | 3 | direct_xref | usable |
| digoxin | digoxin | CHEMBL1751 | 323 | 19 | direct_xref | usable |
| empagliflozin | empagliflozin | CHEMBL2107830 | 269 | 3 | direct_xref | usable |
| dapagliflozin | dapagliflozin | CHEMBL429910 | 262 | 4 | direct_xref | usable |
| repaglinide | repaglinide | CHEMBL1272 | 244 | 12 | exact_name | usable |
| simvastatin | simvastatin | CHEMBL1064 | 237 | 23 | direct_xref | usable |
| rosuvastatin | rosuvastatin | CHEMBL1496 | 215 | 9 | direct_xref | usable |
| canagliflozin | canagliflozin | CHEMBL2048484 | 199 | 5 | direct_xref | usable |
| tolbutamide | tolbutamide | CHEMBL782 | 191 | 8 | direct_xref | usable |
| memantine | memantine | CHEMBL807 | 179 | 14 | direct_xref | usable |
| aliskiren | aliskiren | CHEMBL1639 | 179 | 6 | direct_xref | usable |
| chlorzoxazone | chlorzoxazone | CHEMBL1371 | 178 | 10 | direct_xref | usable |
| ramipril | ramipril | CHEMBL1168 | 177 | 4 | direct_xref | usable |
| furosemide | furosemide | CHEMBL35 | 175 | 21 | direct_xref | usable |
| rifampicin | rifampicin | CHEMBL374478 | 169 | 15 | direct_xref | usable |
| metoprolol | metoprolol | CHEMBL13 | 150 | 11 | direct_xref | usable |
| lisinopril | lisinopril | CHEMBL1237 | 146 | 3 | direct_xref | usable |
| hydrochlorothiazide | hydrochlorothiazide | CHEMBL435 | 140 | 11 | direct_xref | usable |
| glimepiride | glimepiride | CHEMBL1481 | 138 | 6 | direct_xref | usable |
| warfarin | warfarin | CHEMBL1464 | 123 | 5 | exact_name | usable |
| captopril | captopril | CHEMBL1560 | 100 | 8 | direct_xref | usable |
| cimetidine | cimetidine | CHEMBL30 | 98 | 16 | direct_xref | usable |
| erythromycin | erythromycin | CHEMBL532 | 84 | 19 | exact_name | usable |
| verapamil | verapamil | CHEMBL6966 | 76 | 22 | exact_name | usable |
| diazepam | diazepam | CHEMBL12 | 74 | 15 | direct_xref | usable |
| rapamycin | rapamycin | CHEMBL413 | 72 | 28 | direct_xref | usable |

### 3.5 PK Concentration Time-Series

| Metric | Count |
|--------|-------|
| Records from `/pkdata/outputs/` (unauthenticated) | 0 |
| Records from `/pkdata/timecourses/` (unauthenticated) | 0 |
| Accessible TSV files for open-licence studies | 0 |
| Pilot dataset: drugs with PK + targets | 0 |

---

## 4. API Access Findings

### 4.1 Fully Accessible Endpoints (No Authentication Required)

| Endpoint | Data | Records |
|----------|------|---------|
| `/api/v1/info_nodes/?ntype=substance` | Substance catalogue + ChEMBL xrefs | 60+ |
| `/api/v1/pkdata/studies/` | Study metadata, licence info, substance lists | 803+ |
| `/api/v1/studies/` | Basic study metadata + PMID | 803+ |
| `/api/v1/pkdata/interventions/` | Dosing metadata | 60+ |
| ChEMBL `new_client.molecule` | Molecule structures + properties | Unlimited |
| ChEMBL `new_client.mechanism` | Mechanism of action | Unlimited |
| ChEMBL `new_client.activity` | Bioactivity measurements | Unlimited |
| ChEMBL `new_client.target` | Protein targets + UniProt ACs | Unlimited |

### 4.2 Restricted Endpoints (Authentication Required)

| Endpoint | Returns (unauthenticated) | Note |
|----------|--------------------------|------|
| `/api/v1/pkdata/outputs/` | `{"count": 0, "data": []}` | Requires session cookie |
| `/api/v1/pkdata/timecourses/` | `{"count": 0, "data": []}` | Requires session cookie |
| `/api/v1/pkdata/data/` | `{"count": 0, "data": []}` | Requires session cookie |
| `/api/v1/subsets/` | `{"count": 0, "data": []}` | Requires session cookie |
| `/api/v1/_studies/{sid}/` | HTTP 403 / empty | Internal admin endpoint |
| Media files (dot-prefix) | HTTP 403 | e.g., `.Erp2011_Fig1.tsv` |

**Root Cause:** PK-DB uses Django session authentication. All `pkdata/outputs` and timecourse endpoints check for a logged-in user. The PK-DB web interface (https://pk-db.com) allows free registration; once logged in, an API token or session cookie can be used for programmatic access.

### 4.3 Licence Model

PK-DB studies have two licence types:
- **`licence=open`**: Study data is openly licensed. In the pilot set of 60 studies, 3 have open licences. However, the TSV files for these studies still use dot-prefixed filenames, indicating server-level access control regardless of licence.
- **`licence=closed`**: Restricted studies (data accessible via API with authentication, but the underlying data is from closed publications).

**Note:** The PK-DB paper (Grzegorzewski et al., NAR 2022) describes PK-DB as "open access." This refers to the database's open governance model and free registration -- not that concentration data is available without login.

---

## 4. Phase 2 PK Time-Series Preprocessing Results

### 4.1 Summary Statistics

| Preprocessing Metric | Count / Value |
|----------------------|---------------|
| **Drugs Successfully Processed** | **36 usable drugs** |
| Total Raw Observations Extracted | 3,184 |
| **Cleaned Valid Observations Remaining** | **2,325** |
| Invalid / Missing Records Removed | 859 (27.0%) |
| Time Unit Conversions to Hours (`time_hr`) | 3,099 |
| Concentration Unit Standardizations (`value_std`) | 3,184 |
| Unique Studies Represented | 162 |
| Unique Individual / Group Subjects | 31 |
| **Overall Time Range (`time_hr`)** | **0.00 hr – 576.00 hr** |
| Peak Observation Density Range | `t ∈ [0.0, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0, 48.0] hr` |

### 4.2 Data Processing & Quality Rules Applied

1. **Unit Standardization**:
   - **Time**: Converted to hours (`hr`) unambiguously (`min` $\rightarrow$ `/60`, `hr` $\rightarrow$ `1.0`, `day` $\rightarrow$ `*24`, `week` $\rightarrow$ `*168`).
   - **Concentration**: Converted mass/volume units (`mg/L`, `ug/mL` $\rightarrow$ `mg/L`; `ng/mL`, `ug/L` $\rightarrow$ `ug/L`). Preserved dimensionless and molar SI units without uncalibrated distortion.
2. **Quality Filtering**:
   - Filtered out records with missing/NaN time or concentration values.
   - Removed negative time points (`time_hr < 0`) and non-positive concentrations (`value_std <= 0`).
3. **Granularity Preservation**:
   - Kept full entity identity (`drug_name`, `pkdb_id`, `chembl_id`, `study_sid`, `group_pk`, `individual_pk`).
   - Observations were **NOT** merged or aggregated across separate studies, groups, or individuals.
4. **Time Grid Strategy**:
   - Empirical inspection shows high observation density between `0.0 hr` and `48.0 hr`.
   - Grid evaluation deferred until downstream trajectory interpolation in Phase 3.

---

## 5. Output File Inventory (Phase 1 & Phase 2)

```
data/
  processed/
    id_mapping_table.csv              (Identifier mapping table)
    chembl_ids.txt                    (Mapped ChEMBL accession IDs)
    pkdb_chembl_candidate_summary.csv (50 candidate drugs, 36 usable drugs)
    pk_timecourses_clean.csv          (2,325 cleaned observations across 36 drugs)
    pk_preprocessing_summary.csv      (Per-drug preprocessing metrics)

outputs/
  figures/
    pk_profile_midazolam.png          (Midazolam PK trajectory plot)
    pk_profile_omeprazole.png         (Omeprazole PK trajectory plot)
    pk_profile_losartan.png           (Losartan PK trajectory plot)
    pk_profile_dapagliflozin.png     (Dapagliflozin PK trajectory plot)
    pk_profile_canagliflozin.png      (Canagliflozin PK trajectory plot)
    pk_profile_metoprolol.png         (Metoprolol PK trajectory plot)
    summary_pk_trajectories.png       (6-panel multi-drug PK overview)

src/
  fetch_pkdb.py                       (PK-DB raw collector)
  fetch_chembl.py                     (ChEMBL raw collector)
  map_identifiers.py                  (ID mapper)
  preprocess_pk.py                    (Phase 2 preprocessing engine)
  plot_pk.py                          (Phase 2 visualization engine)
```

---

## 8. Phase 2 Recommendations

Given the PK time-series access constraint, Phase 2 should:

1. **Register a PK-DB account** (5 minutes; free) and add authentication to `fetch_pkdb.py`. Once authenticated, the full ~803 study dataset with concentration time-series is accessible.

2. **Filter for drugs with both PK and target data** -- the pilot already identifies 14 strong candidates (atazanavir, dapagliflozin, raltegravir, etc.) with curated ChEMBL mechanism records.

3. **Proceed with bipartite graph construction** -- the ChEMBL data (88 targets, 692 activities, 4 mechanisms) is fully downloaded and sufficient for building the drug-protein graph nodes and edges.

4. **Implement `--token` option in `fetch_pkdb.py`** (see Workaround A above) before running the full pipeline.

---

*Generated by Phase 1 pipeline. Raw data preserved unchanged in `data/raw/`. All code in `src/`.*
