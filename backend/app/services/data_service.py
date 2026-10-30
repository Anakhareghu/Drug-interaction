import pandas as pd
from typing import List, Dict, Any
from app.core.config import settings

def read_csv_safe(path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame()

def get_cohort_summary() -> List[Dict[str, Any]]:
    df = read_csv_safe(settings.COHORT_SUMMARY_FILE)
    return df.to_dict(orient="records")

def get_drugs() -> List[str]:
    df = read_csv_safe(settings.COHORT_SUMMARY_FILE)
    if "drug_name" in df.columns:
        return df["drug_name"].tolist()
    return []

def get_drug_info(drug_name: str) -> Dict[str, Any]:
    df = read_csv_safe(settings.DRUGS_INFO_FILE)
    if df.empty:
        return {}
    drug_data = df[df["drug_name"] == drug_name]
    if drug_data.empty:
        return {}
    return drug_data.iloc[0].to_dict()

def get_pk_trajectories() -> Dict[str, Any]:
    df = read_csv_safe(settings.PK_TRAJECTORY_STATS_FILE)
    if df.empty:
        return {}
    
    result = {}
    for drug_name, group in df.groupby("drug"):
        trajectory = []
        for _, row in group.iterrows():
            trajectory.append({
                "time": row["time"],
                "mean": row["mean"],
                "standard_error": row["standard_error"],
                "dose_norm_mean": row["dose_norm_mean"],
                "peak_norm_mean": row["peak_norm_mean"]
            })
        result[drug_name] = trajectory
    return result

def get_pk_similarity() -> List[Dict[str, Any]]:
    df = read_csv_safe(settings.PK_SIMILARITY_FILE)
    if df.empty:
        return []
    
    similarities = []
    drugs = df.columns[1:]
    for i, row in df.iterrows():
        drug_1 = row.iloc[0]
        for drug_2 in drugs:
            similarities.append({
                "drug_name_1": drug_1,
                "drug_name_2": drug_2,
                "svd_distance_peak": row[drug_2]
            })
    return similarities

def get_network() -> Dict[str, Any]:
    df = read_csv_safe(settings.TARGET_NETWORK_FILE)
    if df.empty:
        return {}
    
    edges = []
    drugs = df.index.tolist()
    targets = df.columns.tolist()
    for i, row in df.iterrows():
        # Handle if drug names are in index or a column
        if "Unnamed: 0" in row.index:
            drug_name = row["Unnamed: 0"]
            valid_targets = [t for t in df.columns if t != "Unnamed: 0"]
        else:
            drug_name = str(i) # Fallback, not correct if no drug name column
            valid_targets = targets
            
        for target in valid_targets:
            if row[target] == 1:
                edges.append({
                    "drug_name": drug_name,
                    "target_id": target
                })
    return {"edges": edges}

def get_clustering() -> List[Dict[str, Any]]:
    df = read_csv_safe(settings.CLUSTERING_FILE)
    return df.to_dict(orient="records")

def get_coupling() -> List[Dict[str, Any]]:
    df = read_csv_safe(settings.COUPLING_FILE)
    return df.to_dict(orient="records")

def get_results() -> List[Dict[str, Any]]:
    df = read_csv_safe(settings.RESULTS_FILE)
    return df.to_dict(orient="records")
