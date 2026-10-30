from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class HealthResponse(BaseModel):
    status: str

class CohortSummaryResponse(BaseModel):
    drug_name: str
    n_human_subjects: int
    n_valid_pk_observations: int

class DrugInfoResponse(BaseModel):
    drug_name: str
    chembl_id: str
    subject_count: int
    observation_count: int
    scientific_adequacy_status: str

class PKTrajectoryPoint(BaseModel):
    time: float
    mean: float
    standard_error: float
    dose_norm_mean: float
    peak_norm_mean: float

class PKTrajectoryResponse(BaseModel):
    drug_name: str
    trajectory: List[PKTrajectoryPoint]

class PKSimilarityResponse(BaseModel):
    drug_name_1: str
    drug_name_2: str
    svd_distance_peak: float

class NetworkEdge(BaseModel):
    drug_name: str
    target_id: str

class ClusteringResponse(BaseModel):
    drug_name: str
    svd_ward_k2: int
    svd_ward_k3: int
    svd_avg_k2: int
    svd_avg_k3: int
    dtw_avg_k2: int
    dtw_avg_k3: int
    kmeans_k2: int
    kmeans_k3: int

class CouplingResultResponse(BaseModel):
    pk_representation: str
    target_representation: str
    n_pairs: int
    spearman_rho: float
    spearman_p_two_tailed: float
    pearson_r: float
    pearson_p_two_tailed: float
    n_permutations: int
    mantel_p_value: float
    coupling_status: str

class IntegratedResultResponse(BaseModel):
    scientific_status: str
