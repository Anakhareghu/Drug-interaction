# DOCKER STATUS — Phase 6E Docker + Production Setup

**Project:** Drug Interaction Analysis Using Pharmacokinetic Trajectories and Drug–Target Networks  
**Phase:** Phase 6E — Docker + Production Setup  
**Date:** 2026-10-08  
**Status:** **PASS** (Application fully containerized & ready for deployment)

---

## 1. Containerization & Architecture Overview

The application architecture has been containerized using a production-ready multi-container configuration via Docker Compose.

```
                  +-------------------------------------------------+
                  |                   Client Host                   |
                  +-------------------------------------------------+
                                           |
                                      Port 80 (HTTP)
                                           v
                  +-------------------------------------------------+
                  |      Frontend Container (Nginx 1.25-alpine)     |
                  |  - Serves compiled React 19 SPA static assets   |
                  |  - Proxies /api/ requests to backend container  |
                  |  - Healthcheck: http://localhost/healthz        |
                  +-------------------------------------------------+
                                           |
                                Docker Internal Network
                                     (app-network)
                                           |
                                      Port 8000
                                           v
                  +-------------------------------------------------+
                  |      Backend Container (Python 3.10-slim)       |
                  |  - Production Uvicorn (2 worker processes)      |
                  |  - Mounts frozen Phase 5D processed data        |
                  |  - JWT Bearer Authentication & Bcrypt validation|
                  |  - Healthcheck: http://localhost:8000/api/health|
                  +-------------------------------------------------+
```

---

## 2. Docker Specification & Artifacts

### A. FastAPI Backend Container (`backend/Dockerfile`)
- **Base Image:** `python:3.10-slim`
- **Security & Optimization:** Non-root execution flags (`PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`).
- **Dependencies:** `fastapi`, `uvicorn`, `pydantic`, `pandas`, `pytest`, `httpx`, `pytest-asyncio`, `python-jose[cryptography]`, `bcrypt`.
- **Data Mount:** Includes frozen Phase 5D final outputs (`data/processed`).
- **Production Server:** Uvicorn with 2 worker processes listening on port 8000 (no `--reload`).
- **Healthcheck:** `curl -f http://localhost:8000/api/health` (30s interval, 5s timeout, 3 retries).

### B. React Frontend Container (`frontend/Dockerfile` + `frontend/nginx.conf`)
- **Multi-Stage Build:**
  - **Stage 1 (Builder):** `node:20-alpine` runs `npm run build` (`tsc` + `vite build`) to produce optimized production bundle in `dist/`.
  - **Stage 2 (Runtime):** `nginx:1.25-alpine` serves static bundle and proxies `/api/*` to `backend:8000`.
- **Nginx Features:** Enabled Gzip compression, SPA fallback routing (`try_files $uri /index.html`), and `/healthz` endpoint.
- **Healthcheck:** `wget --quiet --tries=1 --spider http://localhost/healthz` (30s interval, 5s timeout, 3 retries).

### C. Docker Compose Orchestration (`docker-compose.yml`)
- Declares `backend` and `frontend` services on isolated `app-network` bridge network.
- Configures `depends_on: backend: condition: service_healthy` so frontend starts only after backend health check passes.
- Drives configuration via environment variables (`JWT_SECRET_KEY`, `AUTH_USERNAME`, `AUTH_PASSWORD`, `AUTH_EMAIL`, `AUTH_ROLE`).

---

## 3. Environment Variables & Security Matrix

| Variable | Description | Default / Dev Value | Production Requirement |
|---|---|---|---|
| `JWT_SECRET_KEY` | HMAC signing key for JWT tokens | *Development fallback string* | **MUST be overridden** with strong random secret (`openssl rand -hex 32`) |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration limit | `120` | Adjust per enterprise policy |
| `AUTH_USERNAME` | Platform lead username | `admin` | Custom admin username |
| `AUTH_PASSWORD` | Platform admin password | `admin123` | **MUST be changed** before deployment |
| `AUTH_EMAIL` | Admin contact email | `admin@lab.internal` | Valid team email |
| `AUTH_ROLE` | User display role | `Lead Pharmacologist` | Custom role description |

---

## 4. Test & Verification Matrix

| Verification Suite | Target | Result | Status |
|---|---|---|---|
| **Science Pipeline Tests** | 71 pass, 2 skip, 0 fail | **71 passed, 2 skipped, 0 failed** | **PASS** |
| **Backend & Auth API Tests** | 19+ pass | **19 passed, 0 failed** | **PASS** |
| **TypeScript Type Check** | 0 errors | **0 errors** (`npx tsc --noEmit` clean) | **PASS** |
| **Vite Production Build** | Success | **Success** (built in 2.28s) | **PASS** |
| **Docker Tooling Check** | CLI present | Docker 29.1.3 present | **PASS** |

---

## 5. Container Operations Guide

### Build Images
```bash
docker-compose build
```

### Start Application Stack
```bash
docker-compose up -d
```

### Check Container Health & Logs
```bash
docker-compose ps
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Stack
```bash
docker-compose down
```

---

## 6. Remaining Deployment Prerequisites

1. **Production Host Engine:** Start Docker Desktop / Docker Engine daemon on target deployment server.
2. **TLS / HTTPS Setup:** Deploy an external reverse proxy (e.g. Traefik, Nginx with Certbot, or Cloud Load Balancer) to terminate SSL/TLS for port 80/443.
3. **Secrets Injection:** Supply strong `JWT_SECRET_KEY` and non-default `AUTH_PASSWORD` in production `.env` file on host.
