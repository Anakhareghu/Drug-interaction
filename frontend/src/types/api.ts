// TypeScript interfaces matching the FastAPI backend Pydantic models

export interface HealthResponse {
  status: string;
}

export interface CohortSummary {
  drug_name: string;
  n_human_subjects: number;
  n_valid_pk_observations: number;
}

export interface DrugInfo {
  drug_name: string;
  chembl_id: string;
  subject_count: number;
  observation_count: number;
  scientific_adequacy_status: string;
}

export interface PKTrajectoryPoint {
  time: number;
  mean: number;
  standard_error: number;
  dose_norm_mean: number;
  peak_norm_mean: number;
}

export interface PKTrajectory {
  drug_name: string;
  trajectory: PKTrajectoryPoint[];
}

export interface PKSimilarity {
  drug_name_1: string;
  drug_name_2: string;
  svd_distance_peak: number;
}

export interface NetworkEdge {
  drug_name: string;
  target_id: string;
}

export interface NetworkData {
  edges: NetworkEdge[];
}

export interface ClusteringResult {
  drug_name: string;
  svd_ward_k2: number;
  svd_ward_k3: number;
  svd_avg_k2: number;
  svd_avg_k3: number;
  dtw_avg_k2: number;
  dtw_avg_k3: number;
  kmeans_k2: number;
  kmeans_k3: number;
}

export interface CouplingResult {
  pk_representation: string;
  target_representation: string;
  n_pairs: number;
  spearman_rho: number;
  spearman_p_two_tailed: number;
  pearson_r: number;
  pearson_p_two_tailed: number;
  n_permutations: number;
  mantel_p_value: number;
  coupling_status: string;
}

export interface IntegratedResult {
  scientific_status: string;
}

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export interface AuthUser {
  id: string;
  username: string;
  email?: string | null;
  role: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}
