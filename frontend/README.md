# Drug Interaction Analysis — React Frontend

**Phase 6B — Read-only frontend consuming the frozen Phase 5D research pipeline data via FastAPI.**

## Stack
- **React 19** + **TypeScript**
- **Vite 8** (build tool)
- **Tailwind CSS 4** (via `@tailwindcss/vite` plugin)
- **React Router v7** (client-side routing)
- **Recharts** (scientific charts)
- **Axios** (API calls with centralized error handling)
- **Lucide React** (icons)

## Pages

| Route | Page | Data Source |
|---|---|---|
| `/` | Home | Static |
| `/methodology` | Methodology | Static |
| `/dashboard` | Dashboard | `GET /api/cohort` |
| `/explorer` | Drug Explorer | `GET /api/drugs`, `/api/drugs/{name}`, `/api/pk/trajectories` |
| `/pk-analysis` | PK Analysis | `GET /api/pk/trajectories`, `/api/pk/similarity`, `/api/clustering` |
| `/network` | Network Analysis | `GET /api/network` |
| `/results` | Integrated Results | `GET /api/coupling`, `/api/clustering` |

## Prerequisites

- **Backend** must be running on port 8000 (Phase 6A).
- Node.js ≥ 18.

## Running

### 1. Start the FastAPI backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the React frontend (new terminal)
```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`

## Environment Variable

Backend URL is configured via `frontend/.env`:
```
VITE_API_URL=http://localhost:8000/api
```

The Vite dev server also proxies `/api` → `http://localhost:8000` so requests work in both dev and production modes.

## Project Structure

```
frontend/src/
├── components/
│   ├── ErrorAlert.tsx     — API error display
│   ├── LoadingSpinner.tsx  — Loading state
│   ├── Sidebar.tsx        — Navigation sidebar
│   └── StatCard.tsx       — KPI metric card
├── pages/
│   ├── Home.tsx
│   ├── Methodology.tsx
│   ├── Dashboard.tsx
│   ├── DrugExplorer.tsx
│   ├── PKAnalysis.tsx
│   ├── NetworkAnalysis.tsx
│   └── IntegratedResults.tsx
├── services/
│   └── api.ts             — Centralized Axios API layer
├── types/
│   └── api.ts             — TypeScript interfaces for all API responses
├── App.tsx                — Router + layout
├── main.tsx               — React entry point
└── index.css              — Tailwind v4 + CSS variables
```
