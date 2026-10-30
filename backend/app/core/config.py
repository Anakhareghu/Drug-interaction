import os
from pathlib import Path
from pydantic import BaseModel
from typing import List

def get_cors_origins() -> List[str]:
    cors_str = os.getenv("CORS_ORIGINS")
    if cors_str:
        return [origin.strip() for origin in cors_str.split(",") if origin.strip()]
    return [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

class Settings(BaseModel):
    PROJECT_NAME: str = "Drug Interaction Analysis API"
    API_V1_STR: str = "/api"
    
    # Security / Auth settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "pharmaco-kinetic-target-network-insecure-dev-secret-key-change-in-prod-2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    
    # Default admin credentials for research platform access
    DEFAULT_AUTH_USERNAME: str = os.getenv("AUTH_USERNAME", "admin")
    DEFAULT_AUTH_PASSWORD: str = os.getenv("AUTH_PASSWORD", "admin123")
    DEFAULT_AUTH_EMAIL: str = os.getenv("AUTH_EMAIL", "researcher@lab.internal")
    DEFAULT_AUTH_ROLE: str = os.getenv("AUTH_ROLE", "Lead Pharmacologist")
    
    # Allowed CORS Origins (environment customizable)
    CORS_ORIGINS: List[str] = get_cors_origins()
    
    # Base paths
    BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent
    PROJECT_DIR: Path = BACKEND_DIR.parent
    DATA_DIR: Path = PROJECT_DIR / "data" / "processed"
    FINAL_DIR: Path = DATA_DIR / "final"
    PHASE5C_DIR: Path = DATA_DIR / "phase5c"
    
    # Specific file paths
    COHORT_SUMMARY_FILE: Path = FINAL_DIR / "final_cohort_summary.csv"
    DRUGS_INFO_FILE: Path = DATA_DIR / "phase4d_adequacy_summary.csv"
    PK_TRAJECTORY_STATS_FILE: Path = DATA_DIR / "pk_phase5_trajectory_statistics.csv"
    PK_SIMILARITY_FILE: Path = PHASE5C_DIR / "pk_svd_distance_peak.csv"
    TARGET_NETWORK_FILE: Path = PHASE5C_DIR / "chembl_target_bipartite_matrix.csv"
    CLUSTERING_FILE: Path = PHASE5C_DIR / "clustering_assignments.csv"
    COUPLING_FILE: Path = PHASE5C_DIR / "pk_target_coupling_results.csv"
    RESULTS_FILE: Path = FINAL_DIR / "final_integrated_results.csv"

settings = Settings()
