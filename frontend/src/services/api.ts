/// <reference types="vite/client" />
import axios from 'axios';
import type {
  CohortSummary, DrugInfo, PKTrajectory, PKSimilarity,
  NetworkData, ClusteringResult, CouplingResult, IntegratedResult,
  LoginCredentials, TokenResponse, AuthUser
} from '../types/api';

// Use Vite proxy or env configured backend URL
const BASE = import.meta.env.VITE_API_URL ?? '/api';

export const TOKEN_STORAGE_KEY = 'pk_auth_token';
export const USER_STORAGE_KEY = 'pk_auth_user';

const client = axios.create({ baseURL: BASE, timeout: 10000 });

// Request interceptor to automatically attach JWT Bearer token
client.interceptors.request.use(config => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for consistent error handling and session expiration detection
client.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      // If unauthorized on a protected route or session expired
      const token = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (token && !err.config?.url?.includes('/auth/login')) {
        // Clear expired session and dispatch session expired event
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
        window.dispatchEvent(new CustomEvent('auth:expired', { detail: 'Your session has expired. Please log in again.' }));
      }
    }
    const msg = err.response?.data?.detail ?? err.message ?? 'API error';
    return Promise.reject(new Error(msg));
  }
);

// Authentication Endpoints
export const loginApi = (credentials: LoginCredentials): Promise<TokenResponse> =>
  client.post<TokenResponse>('/auth/login', credentials).then(r => r.data);

export const getCurrentUserApi = (): Promise<AuthUser> =>
  client.get<AuthUser>('/auth/me').then(r => r.data);

export const logoutApi = (): Promise<{ message: string }> =>
  client.post<{ message: string }>('/auth/logout').then(r => r.data);

// Research Data Endpoints
export const getHealth    = ()                    => client.get<{status:string}>('/health').then(r => r.data);
export const getCohort    = ()                    => client.get<CohortSummary[]>('/cohort').then(r => r.data);
export const getDrugs     = ()                    => client.get<string[]>('/drugs').then(r => r.data);
export const getDrugInfo  = (name: string)        => client.get<DrugInfo>(`/drugs/${name}`).then(r => r.data);
export const getTrajectories = ()                 => client.get<PKTrajectory[]>('/pk/trajectories').then(r => r.data);
export const getSimilarity = ()                   => client.get<PKSimilarity[]>('/pk/similarity').then(r => r.data);
export const getNetwork   = ()                    => client.get<NetworkData>('/network').then(r => r.data);
export const getClustering = ()                   => client.get<ClusteringResult[]>('/clustering').then(r => r.data);
export const getCoupling  = ()                    => client.get<CouplingResult[]>('/coupling').then(r => r.data);
export const getResults   = ()                    => client.get<IntegratedResult[]>('/results').then(r => r.data);
