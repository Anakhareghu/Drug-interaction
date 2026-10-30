from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services import data_service
from app.models.data_models import (
    HealthResponse,
    CohortSummaryResponse,
    DrugInfoResponse,
    PKTrajectoryResponse,
    PKTrajectoryPoint,
    PKSimilarityResponse,
    ClusteringResponse,
    CouplingResultResponse,
    IntegratedResultResponse
)

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    return {"status": "ok"}

@router.get("/cohort", response_model=List[CohortSummaryResponse])
def get_cohort():
    data = data_service.get_cohort_summary()
    if not data:
        raise HTTPException(status_code=404, detail="Cohort data not found")
    return data

@router.get("/drugs", response_model=List[str])
def get_drugs():
    drugs = data_service.get_drugs()
    if not drugs:
        raise HTTPException(status_code=404, detail="Drugs not found")
    return drugs

@router.get("/drugs/{drug_name}", response_model=DrugInfoResponse)
def get_drug(drug_name: str):
    drug_info = data_service.get_drug_info(drug_name)
    if not drug_info:
        raise HTTPException(status_code=404, detail=f"Drug {drug_name} not found")
    return drug_info

@router.get("/pk/trajectories", response_model=List[PKTrajectoryResponse])
def get_trajectories():
    trajectories = data_service.get_pk_trajectories()
    if not trajectories:
        raise HTTPException(status_code=404, detail="Trajectories not found")
    return [{"drug_name": k, "trajectory": v} for k, v in trajectories.items()]

@router.get("/pk/similarity", response_model=List[PKSimilarityResponse])
def get_similarity():
    similarity = data_service.get_pk_similarity()
    if not similarity:
        raise HTTPException(status_code=404, detail="Similarity data not found")
    return similarity

@router.get("/network")
def get_network():
    network = data_service.get_network()
    if not network:
        raise HTTPException(status_code=404, detail="Network data not found")
    return network

@router.get("/clustering", response_model=List[ClusteringResponse])
def get_clustering():
    clustering = data_service.get_clustering()
    if not clustering:
        raise HTTPException(status_code=404, detail="Clustering data not found")
    return clustering

@router.get("/coupling", response_model=List[CouplingResultResponse])
def get_coupling():
    coupling = data_service.get_coupling()
    if not coupling:
        raise HTTPException(status_code=404, detail="Coupling data not found")
    return coupling

@router.get("/results", response_model=List[IntegratedResultResponse])
def get_results():
    results = data_service.get_results()
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    return results
