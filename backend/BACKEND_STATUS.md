# PHASE 6A — FASTAPI BACKEND

**Project:** Drug Interaction Analysis Using Pharmacokinetic Trajectories and Drug–Target Networks  
**Phase:** Phase 6A — FastAPI Backend  
**Date:** 2026-10-08  
**Status:** COMPLETE & VALIDATED (`PHASE 6A STATUS = PASS`)  

---

## 1. Architecture
- **Framework:** FastAPI
- **Language:** Python
- **Structure:** Modular architecture separated into:
  - `app/api/`: API Routes
  - `app/services/`: Data access logic
  - `app/models/`: Pydantic schemas for request/response typing
  - `app/core/`: Configuration and global settings
- **Configuration:** Static, stateless backend configured to read precisely from the frozen Phase 5D master CSV files.
- **CORS:** Enabled (`*`) to support the future React frontend development.

## 2. Endpoints Implemented
- `GET /api/health` — API liveness check.
- `GET /api/cohort` — Final validated cohort summary.
- `GET /api/drugs` — List of the 7 drug names.
- `GET /api/drugs/{drug_name}` — Comprehensive information for a single drug.
- `GET /api/pk/trajectories` — Standardized 15-point PK trajectory data for all drugs.
- `GET /api/pk/similarity` — Pairwise PK distance/similarity metrics.
- `GET /api/network` — Binary ChEMBL drug-target bipartite network edges.
- `GET /api/clustering` — Validated cluster assignments and stability metrics.
- `GET /api/coupling` — PK-target non-parametric Mantel matrix permutation correlations.
- `GET /api/results` — Final, consolidated integrated results table.

## 3. Data Sources
All API responses are dynamically served from the static `.csv` datasets residing in `data/processed/`.
No modifications, recomputations, or mathematical alterations to the frozen scientific pipeline are performed by this layer.

## 4. How to Run
1. **Install Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. **Start the Development Server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
3. **Explore OpenAPI Documentation:**
   Navigate to `http://localhost:8000/api/openapi.json` or `http://localhost:8000/docs`.

## 5. Tests
- **Framework:** Pytest + FastAPI TestClient
- **Coverage:** Tested health, all data retrieval endpoints, and invalid `404` drug queries.
- **Execution:** 
  ```bash
  cd backend
  pytest
  ```

## 6. Current Status
The backend REST API is fully implemented, serving the frozen scientific pipeline data exclusively as read-only endpoints. The system is ready to be consumed by the React frontend (Phase 6B).
